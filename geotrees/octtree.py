"""
Constructors for OctTree classes that can decrease the number of comparisons
for detecting nearby records for example. This is an implementation that uses
Haversine distances for comparisons between records for identification of
neighbours.
"""

import datetime
from typing import List, Optional

from geotrees.record import SpaceTimeRecord
from geotrees.shape import SpaceTimeEllipse, SpaceTimeRectangle


class OctTree:
    """
    Acts as a space-time OctTree on the surface of Earth, allowing for querying
    nearby points faster than searching a full DataFrame. As SpaceTimeRecords
    are added to the OctTree, the OctTree divides into 8 branches as the
    capacity is reached, points within the OctTree are not distributed to the
    branch OctTrees. Additional SpaceTimeRecords are then added to the branch
    where they fall within the branch OctTree's boundary.

    Whilst the OctTree has a temporal component, and was designed to utilise
    datetime / timedelta objects, numeric values and ranges can be used. This
    usage must be consistent for the boundary and all SpaceTimeRecords that
    are part of the OctTree. This allows for usage of pentad, timestamp,
    Julian day, etc. as datetime values.

    Parameters
    ----------
    boundary : SpaceTimeRectangle
        The bounding SpaceTimeRectangle of the QuadTree
    capacity : int
        The capacity of each cell, if max_depth is set then a cell at the
        maximum depth may contain more points than the capacity.
    depth : int
        The current depth of the cell. Initialises to zero if unset.
    max_depth : int | None
        The maximum depth of the QuadTree. If set, this can override the
        capacity for cells at the maximum depth.
    """

    def __init__(
        self,
        boundary: SpaceTimeRectangle,
        capacity: int = 5,
        depth: int = 0,
        max_depth: Optional[int] = None,
    ) -> None:
        self.boundary = boundary
        self.capacity = capacity
        self.depth = depth
        self.max_depth = max_depth
        self.points: list[SpaceTimeRecord] = list()
        self.divided: bool = False
        return None

    def __str__(self) -> str:
        indent = "    " * self.depth
        out = f"{indent}OctTree:\n"
        out += f"{indent}- boundary: {self.boundary}\n"
        out += f"{indent}- capacity: {self.capacity}\n"
        out += f"{indent}- depth: {self.depth}\n"
        if self.max_depth:
            out += f"{indent}- max_depth: {self.max_depth}\n"
        if self.points:
            out += f"{indent}- contents:\n"
            out += f"{indent}- number of elements: {len(self.points)}\n"
            for p in self.points:
                out += f"{indent}  * {p}\n"
        if self.divided:
            out += f"{indent}- with branches:\n"
            out += f"{self.northwestback}"
            out += f"{self.northeastback}"
            out += f"{self.southwestback}"
            out += f"{self.southeastback}"
            out += f"{self.northwestfwd}"
            out += f"{self.northeastfwd}"
            out += f"{self.southwestfwd}"
            out += f"{self.southeastfwd}"
        return out

    def len(self, current_len: int = 0) -> int:
        """Get the number of points in the OctTree"""
        current_len += len(self.points)
        if not self.divided:
            return current_len

        current_len = self.northeastback.len(current_len)
        current_len = self.northwestback.len(current_len)
        current_len = self.southeastback.len(current_len)
        current_len = self.southwestback.len(current_len)
        current_len = self.northeastfwd.len(current_len)
        current_len = self.northwestfwd.len(current_len)
        current_len = self.southeastfwd.len(current_len)
        current_len = self.southwestfwd.len(current_len)

        return current_len

    def divide(self):
        """Divide the QuadTree"""
        self.northwestfwd = OctTree(
            SpaceTimeRectangle(
                self.boundary.west,
                self.boundary.lon,
                self.boundary.lat,
                self.boundary.north,
                self.boundary.centre_datetime,
                self.boundary.end,
            ),
            capacity=self.capacity,
            depth=self.depth + 1,
            max_depth=self.max_depth,
        )
        self.northeastfwd = OctTree(
            SpaceTimeRectangle(
                self.boundary.lon,
                self.boundary.east,
                self.boundary.lat,
                self.boundary.north,
                self.boundary.centre_datetime,
                self.boundary.end,
            ),
            capacity=self.capacity,
            depth=self.depth + 1,
            max_depth=self.max_depth,
        )
        self.southwestfwd = OctTree(
            SpaceTimeRectangle(
                self.boundary.west,
                self.boundary.lon,
                self.boundary.south,
                self.boundary.lat,
                self.boundary.centre_datetime,
                self.boundary.end,
            ),
            capacity=self.capacity,
            depth=self.depth + 1,
            max_depth=self.max_depth,
        )
        self.southeastfwd = OctTree(
            SpaceTimeRectangle(
                self.boundary.lon,
                self.boundary.east,
                self.boundary.south,
                self.boundary.lat,
                self.boundary.centre_datetime,
                self.boundary.end,
            ),
            capacity=self.capacity,
            depth=self.depth + 1,
            max_depth=self.max_depth,
        )
        self.northwestback = OctTree(
            SpaceTimeRectangle(
                self.boundary.west,
                self.boundary.lon,
                self.boundary.lat,
                self.boundary.north,
                self.boundary.start,
                self.boundary.centre_datetime,
            ),
            capacity=self.capacity,
            depth=self.depth + 1,
            max_depth=self.max_depth,
        )
        self.northeastback = OctTree(
            SpaceTimeRectangle(
                self.boundary.lon,
                self.boundary.east,
                self.boundary.lat,
                self.boundary.north,
                self.boundary.start,
                self.boundary.centre_datetime,
            ),
            capacity=self.capacity,
            depth=self.depth + 1,
            max_depth=self.max_depth,
        )
        self.southwestback = OctTree(
            SpaceTimeRectangle(
                self.boundary.west,
                self.boundary.lon,
                self.boundary.south,
                self.boundary.lat,
                self.boundary.start,
                self.boundary.centre_datetime,
            ),
            capacity=self.capacity,
            depth=self.depth + 1,
            max_depth=self.max_depth,
        )
        self.southeastback = OctTree(
            SpaceTimeRectangle(
                self.boundary.lon,
                self.boundary.east,
                self.boundary.south,
                self.boundary.lat,
                self.boundary.start,
                self.boundary.centre_datetime,
            ),
            capacity=self.capacity,
            depth=self.depth + 1,
            max_depth=self.max_depth,
        )
        self.divided = True
        self.redistribute_to_branches()

    def insert_into_branch(self, point: SpaceTimeRecord) -> bool:
        """
        Insert a point into a branch OctTree.

        Parameters
        ----------
        point : SpaceTimeRecord
            The point to insert

        Returns
        -------
        bool
            True if the point was inserted into a branch OctTree
        """
        if not self.divided:
            self.divide()

        if self.northwestback.insert(point):
            return True
        elif self.northeastback.insert(point):
            return True
        elif self.southwestback.insert(point):
            return True
        elif self.southeastback.insert(point):
            return True
        elif self.northwestfwd.insert(point):
            return True
        elif self.northeastfwd.insert(point):
            return True
        elif self.southwestfwd.insert(point):
            return True
        elif self.southeastfwd.insert(point):
            return True
        return False

    def redistribute_to_branches(self) -> None:
        """Redistribute all points to branches"""
        if not self.divided:
            self.divide()
        while self.points:
            point = self.points.pop()
            self.insert_into_branch(point)
        return None

    def insert(self, point: SpaceTimeRecord) -> bool:
        """
        Insert a point into the OctTree.

        Parameters
        ----------
        point : SpaceTimSpaceTimeeRecord
            The point to insert

        Returns
        -------
        bool
            True if the point was inserted into the OctTree
        """
        if not self.boundary.contains(point):
            return False

        if not self.divided:
            if (len(self.points) < self.capacity) or (
                self.max_depth and self.depth == self.max_depth
            ):
                self.points.append(point)
                return True

        if not self.divided:
            self.divide()

        return self.insert_into_branch(point)

    def remove(self, point: SpaceTimeRecord) -> bool:  # noqa: C901
        """
        Remove a SpaceTimeRecord from the OctTree if it is in the OctTree.

        Parameters
        ----------
        point : SpaceTimeRecord
            The point to remove

        Returns
        -------
        bool
            True if the point is removed
        """
        if not self.boundary.contains(point):
            return False

        # Points are only in leaf nodes
        if not self.divided:
            if point in self.points:
                self.points.remove(point)
                return True
            return False

        if self.northwestback.remove(point):
            return True
        elif self.northeastback.remove(point):
            return True
        elif self.southwestback.remove(point):
            return True
        elif self.southeastback.remove(point):
            return True
        elif self.northwestfwd.remove(point):
            return True
        elif self.northeastfwd.remove(point):
            return True
        elif self.southwestfwd.remove(point):
            return True
        elif self.southeastfwd.remove(point):
            return True

        return False

    def query(
        self,
        rect: SpaceTimeRectangle,
        points: Optional[List[SpaceTimeRecord]] = None,
    ) -> List[SpaceTimeRecord]:
        """
        Get SpaceTimeRecords contained within the OctTree that fall in a
        SpaceTimeRectangle

        Parameters
        ----------
        rect : SpaceTimeRectangle

        Returns
        -------
        List[SpaceTimeRecord]
            The SpaceTimeRecord values contained within the OctTree that fall
            within the bounds of rect.
        """
        if not points:
            points = list()
        if not self.boundary.intersects(rect):
            return points

        # Points are only in leaf nodes
        if not self.divided:
            for point in self.points:
                if rect.contains(point):
                    points.append(point)
            return points

        points = self.northwestfwd.query(rect, points)
        points = self.northeastfwd.query(rect, points)
        points = self.southwestfwd.query(rect, points)
        points = self.southeastfwd.query(rect, points)
        points = self.northwestback.query(rect, points)
        points = self.northeastback.query(rect, points)
        points = self.southwestback.query(rect, points)
        points = self.southeastback.query(rect, points)

        return points

    def query_ellipse(
        self,
        ellipse: SpaceTimeEllipse,
        points: Optional[List[SpaceTimeRecord]] = None,
    ) -> List[SpaceTimeRecord]:
        """
        Get SpaceTimeRecords contained within the OctTree that fall in a
        SpaceTimeEllipse

        Parameters
        ----------
        ellipse : SpaceTimeEllipse

        Returns
        -------
        List[SpaceTimeRecord]
            The SpaceTimeRecord values contained within the OctTree that fall
            within the bounds of ellipse.
        """
        if not points:
            points = list()
        if not ellipse.nearby_rect(self.boundary):
            return points

        # Points are only in leaf nodes
        if not self.divided:
            for point in self.points:
                if ellipse.contains(point):
                    points.append(point)
            return points

        points = self.northwestfwd.query_ellipse(ellipse, points)
        points = self.northeastfwd.query_ellipse(ellipse, points)
        points = self.southwestfwd.query_ellipse(ellipse, points)
        points = self.southeastfwd.query_ellipse(ellipse, points)
        points = self.northwestback.query_ellipse(ellipse, points)
        points = self.northeastback.query_ellipse(ellipse, points)
        points = self.southwestback.query_ellipse(ellipse, points)
        points = self.southeastback.query_ellipse(ellipse, points)

        return points

    def nearby_points(
        self,
        point: SpaceTimeRecord,
        dist: float,
        t_dist: datetime.timedelta,
        points: Optional[List[SpaceTimeRecord]] = None,
        exclude_self: bool = False,
    ) -> List[SpaceTimeRecord]:
        """
        Get all SpaceTimeRecords contained in the OctTree that are nearby
        another query SpaceTimeRecord.

        Query the OctTree to find all SpaceTimeRecords within the OctTree that
        are nearby to the query SpaceTimeRecord. This search should be faster
        than searching through all records, since only OctTree branch whose
        boundaries are close to the query SpaceTimeRecord are evaluated.

        Parameters
        ----------
        point : SpaceTimeRecord
            The query point.
        dist : float
            The distance for comparison. Note that Haversine distance is used
            as the distance metric as the query SpaceTimeRecord and OctTree are
            assumed to lie on the surface of Earth.
        t_dist : datetime.timedelta
            Max time gap between SpaceTimeRecords within the OctTree and the
            query SpaceTimeRecord. Can be numeric if the OctTree boundaries,
            SpaceTimeRecords, and query SpaceTimeRecord have numeric datetime
            values and ranges.
        points : List[SpaceTimeRecord] | None
            List of SpaceTimeRecords already found. Most use cases will be to
            not set this value, since it's main use is for passing onto the
            branch OctTrees.
        exclude_self : bool
            Optionally exclude the query point from the results if the query
            point is in the OctTree

        Returns
        -------
        list[SpaceTimeRecord]
            A list of SpaceTimeRecords whose distance to the
            query SpaceTimeRecord is <= dist, and the datetimes of the
            SpaceTimeRecords fall within the datetime range of the query
            SpaceTimeRecord.
        """
        if not points:
            points = list()
        if not self.boundary.nearby(point, dist, t_dist):
            return points

        # Points are only in leaf nodes
        if not self.divided:
            for test_point in self.points:
                if (
                    test_point.distance(point) <= dist
                    and test_point.datetime <= point.datetime + t_dist
                    and test_point.datetime >= point.datetime - t_dist
                ):
                    if exclude_self and point == test_point:
                        continue
                    points.append(test_point)
            return points

        points = self.northwestback.nearby_points(
            point, dist, t_dist, points, exclude_self
        )
        points = self.northeastback.nearby_points(
            point, dist, t_dist, points, exclude_self
        )
        points = self.southwestback.nearby_points(
            point, dist, t_dist, points, exclude_self
        )
        points = self.southeastback.nearby_points(
            point, dist, t_dist, points, exclude_self
        )
        points = self.northwestfwd.nearby_points(
            point, dist, t_dist, points, exclude_self
        )
        points = self.northeastfwd.nearby_points(
            point, dist, t_dist, points, exclude_self
        )
        points = self.southwestfwd.nearby_points(
            point, dist, t_dist, points, exclude_self
        )
        points = self.southeastfwd.nearby_points(
            point, dist, t_dist, points, exclude_self
        )

        return points
