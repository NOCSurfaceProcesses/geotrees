"""
Constructors for QuadTree classes that can decrease the number of comparisons
for detecting nearby records for example. This is an implementation that uses
Haversine distances for comparisons between records for identification of
neighbours.
"""

from typing import List, Optional

from geotrees.record import Record
from geotrees.shape import Ellipse, Rectangle


class QuadTree:
    """
    Acts as a Geo-spatial QuadTree on the surface of Earth, allowing
    for querying nearby points faster than searching a full DataFrame. As
    Records are added to the QuadTree, the QuadTree divides into 4 branches as
    the capacity is reached, points contained within the QuadTree are not
    distributed to the branch QuadTrees. Additional Records are then added to
    the branch where they fall within the branch QuadTree's boundary.

    Parameters
    ----------
    boundary : Rectangle
        The bounding Rectangle of the QuadTree
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
        boundary: Rectangle,
        capacity: int = 5,
        depth: int = 0,
        max_depth: Optional[int] = None,
    ) -> None:
        self.boundary = boundary
        self.capacity = capacity
        self.depth = depth
        self.max_depth = max_depth
        self.points: List[Record] = list()
        self.divided: bool = False
        return None

    def __str__(self) -> str:
        indent = "    " * self.depth
        out = f"{indent}QuadTree:\n"
        out += f"{indent}- boundary: {self.boundary}\n"
        out += f"{indent}- capacity: {self.capacity}\n"
        out += f"{indent}- depth: {self.depth}\n"
        if self.max_depth:
            out += f"{indent}- max_depth: {self.max_depth}\n"
        out += f"{indent}- contents: {self.points}\n"
        if self.divided:
            out += f"{indent}- with branches:\n"
            out += f"{self.northwest}"
            out += f"{self.northeast}"
            out += f"{self.southwest}"
            out += f"{self.southeast}"
        return out

    def len(self, current_len: int = 0) -> int:
        """Get the number of points in the QuadTree"""
        # Points are only in leaf nodes
        if not self.divided:
            return current_len + len(self.points)

        current_len = self.northeast.len(current_len)
        current_len = self.northwest.len(current_len)
        current_len = self.southeast.len(current_len)
        current_len = self.southwest.len(current_len)

        return current_len

    def divide(self) -> None:
        """Divide the QuadTree"""
        self.northwest = QuadTree(
            Rectangle(
                self.boundary.west,
                self.boundary.lon,
                self.boundary.lat,
                self.boundary.north,
            ),
            capacity=self.capacity,
            depth=self.depth + 1,
            max_depth=self.max_depth,
        )
        self.northeast = QuadTree(
            Rectangle(
                self.boundary.lon,
                self.boundary.east,
                self.boundary.lat,
                self.boundary.north,
            ),
            capacity=self.capacity,
            depth=self.depth + 1,
            max_depth=self.max_depth,
        )
        self.southwest = QuadTree(
            Rectangle(
                self.boundary.west,
                self.boundary.lon,
                self.boundary.south,
                self.boundary.lat,
            ),
            capacity=self.capacity,
            depth=self.depth + 1,
            max_depth=self.max_depth,
        )
        self.southeast = QuadTree(
            Rectangle(
                self.boundary.lon,
                self.boundary.east,
                self.boundary.south,
                self.boundary.lat,
            ),
            capacity=self.capacity,
            depth=self.depth + 1,
            max_depth=self.max_depth,
        )
        self.divided = True
        self.redistribute_to_branches()

    def insert_into_branch(self, point: Record) -> bool:
        """
        Insert a point into a branch QuadTree.

        Parameters
        ----------
        point : Record
            The point to insert

        Returns
        -------
        bool
            True if the point was inserted into a branch QuadTree
        """
        if not self.divided:
            self.divide()

        if self.northwest.insert(point):
            return True
        elif self.northeast.insert(point):
            return True
        elif self.southwest.insert(point):
            return True
        elif self.southeast.insert(point):
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

    def insert(self, point: Record) -> bool:
        """
        Insert a point into the QuadTree.

        Parameters
        ----------
        point : Record
            The point to insert

        Returns
        -------
        bool
            True if the point was inserted into the QuadTree
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

    def remove(self, point: Record) -> bool:
        """
        Remove a Record from the QuadTree if it is in the QuadTree.

        Parameters
        ----------
        point : Record
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

        if self.northwest.remove(point):
            return True
        elif self.northeast.remove(point):
            return True
        elif self.southwest.remove(point):
            return True
        elif self.southeast.remove(point):
            return True

        return False

    def query(
        self,
        rect: Rectangle,
        points: Optional[List[Record]] = None,
    ) -> List[Record]:
        """
        Get Records contained within the QuadTree that fall in a
        Rectangle

        Parameters
        ----------
        rect : Rectangle

        Returns
        -------
        list[Record]
            The Record values contained within the QuadTree that fall
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

        points = self.northwest.query(rect, points)
        points = self.northeast.query(rect, points)
        points = self.southwest.query(rect, points)
        points = self.southeast.query(rect, points)

        return points

    def query_ellipse(
        self,
        ellipse: Ellipse,
        points: Optional[List[Record]] = None,
    ) -> List[Record]:
        """
        Get Records contained within the QuadTree that fall in a
        Ellipse

        Parameters
        ----------
        ellipse : Ellipse

        Returns
        -------
        list[Record]
            The Record values contained within the QuadTree that fall
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

        points = self.northwest.query_ellipse(ellipse, points)
        points = self.northeast.query_ellipse(ellipse, points)
        points = self.southwest.query_ellipse(ellipse, points)
        points = self.southeast.query_ellipse(ellipse, points)

        return points

    def nearby_points(
        self,
        point: Record,
        dist: float,
        points: Optional[List[Record]] = None,
        exclude_self: bool = False,
    ) -> List[Record]:
        """
        Get all Records contained in the QuadTree that are nearby
        another query Record.

        Query the QuadTree to find all Records within the QuadTree that
        are nearby to the query Record. This search should be faster
        than searching through all records, since only QuadTree branch whose
        boundaries are close to the query Record are evaluated.

        Parameters
        ----------
        point : Record
            The query point.
        dist : float
            The distance for comparison. Note that Haversine distance is used
            as the distance metric as the query Record and QuadTree are
            assumed to lie on the surface of Earth.
        points : Records | None
            List of Records already found. Most use cases will be to
            not set this value, since it's main use is for passing onto the
            branch QuadTrees.
        exclude_self : bool
            Optionally exclude the query point from the results if the query
            point is in the OctTree

        Returns
        -------
        list[Record]
            A list of Records whose distance to the
            query Record is <= dist, and the datetimes of the
            Records fall within the datetime range of the query
            Record.
        """
        if not points:
            points = list()
        if not self.boundary.nearby(point, dist):
            return points

        # Points are only in leaf nodes
        if not self.divided:
            for test_point in self.points:
                if test_point.distance(point) <= dist:
                    if exclude_self and point == test_point:
                        continue
                    points.append(test_point)
            return points

        points = self.northwest.nearby_points(point, dist, points, exclude_self)
        points = self.northeast.nearby_points(point, dist, points, exclude_self)
        points = self.southwest.nearby_points(point, dist, points, exclude_self)
        points = self.southeast.nearby_points(point, dist, points, exclude_self)

        return points
