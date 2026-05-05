# Copyright 2025 National Oceanography Centre UK
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Constructors for QuadTree classes that can decrease the number of comparisons
for detecting nearby records for example. This is an implementation that uses
Haversine distances for comparisons between records for identification of
neighbours.
"""

from typing import Dict, List, Optional, Tuple
from warnings import warn

import polars as pl

from geotrees.distance_metrics import haversine_polars
from geotrees.record import Record
from geotrees.shape import Ellipse, Rectangle


_MIN_SCHEMA = pl.Schema(
    {
        "uid": pl.String,
        "lat": pl.Float64,
        "lon": pl.Float64,
    }
)


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
            for branch in self.branches:
                out += f"{branch}"
        return out

    def len(self, current_len: int = 0) -> int:
        """Get the number of points in the QuadTree"""
        # Points are only in leaf nodes
        if not self.divided:
            return current_len + len(self.points)

        for branch in self.branches:
            current_len = branch.len(current_len)

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
        self.branches: List[QuadTree] = [
            self.northwest,
            self.northeast,
            self.southwest,
            self.southeast,
        ]
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

        for branch in self.branches:
            if branch.insert(point):
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

        for branch in self.branches:
            if branch.remove(point):
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

        for branch in self.branches:
            points = branch.query(rect, points)

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

        for branch in self.branches:
            points = branch.query_ellipse(ellipse, points)

        return points

    def nearby_points(
        self,
        point: Record,
        dist: float,
        points: Optional[List[Record]] = None,
        exclude_self: bool = False,
        min_dist: float = 0.0,
    ) -> List[Record]:
        """
        Get all Records contained in the QuadTree that are nearby
        another query Record.

        Query the QuadTree to find all Records within the QuadTree that
        are nearby to the query Record. This search should be faster
        than searching through all records, since only QuadTree branch whose
        boundaries are close to the query Record are evaluated.

        A 'dist' attribute is added to the resulting Records, for convenience,
        saving re-computation as a later step.

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
            point is in the QuadTree
        min_dist : float
            Minimum distance used in comparison. Any points with distance less
            than this value will not be returned. Defaults to 0.0.

        Returns
        -------
        list[Record]
            A list of Records whose distance to the query Record is between
            min_dist and dist. The computed distance value is added to each
            returned Record.
        """
        if not points:
            points = list()
        if not self.boundary.nearby(point, dist):
            return points

        # Points are only in leaf nodes
        if not self.divided:
            for test_point in self.points:
                test_distance = test_point.distance(point)
                if min_dist <= test_distance <= dist:
                    if exclude_self and point == test_point:
                        continue
                    setattr(test_point, "dist", test_distance)
                    points.append(test_point)
            return points

        for branch in self.branches:
            points = branch.nearby_points(
                point,
                dist=dist,
                points=points,
                exclude_self=exclude_self,
                min_dist=min_dist,
            )

        return points


class PolarsQuadTree:
    """A QuadTree using Polars Frames as inputs"""

    def __init__(
        self,
        boundary: Rectangle,
        capacity: int = 5,
        depth: int = 0,
        max_depth: Optional[int] = None,
    ) -> None:
        self.boundary = boundary
        # if self.boundary.wraps:
        #     raise ValueError(
        #         "Boundary must not cross -180, 180 line for PolarsQuadTree"
        #     )
        self.capacity = capacity
        self.depth = depth
        self.max_depth = max_depth
        self.data: Optional[pl.DataFrame] = None
        self.divided: bool = False
        return None

    @property
    def uids(self) -> list[str]:
        """UIDS from the data"""
        if self.data is None:
            return []
        return self.data.get_column("uid").to_list()

    def __str__(self) -> str:
        indent = "    " * self.depth
        out = f"{indent}QuadTree:\n"
        out += f"{indent}- boundary: {self.boundary}\n"
        out += f"{indent}- capacity: {self.capacity}\n"
        out += f"{indent}- depth: {self.depth}\n"
        if self.max_depth:
            out += f"{indent}- max_depth: {self.max_depth}\n"
        if self.data is not None:
            out += f"{indent}- contents: {self.data}\n"
        if self.divided:
            out += f"{indent}- with branches:\n"
            for branch in self.branches:
                out += f"{branch}"
        return out

    def len(self, current_len: int = 0) -> int:
        """Get the number of points in the QuadTree"""
        # Points are only in leaf nodes
        if not self.divided:
            if self.data is None:
                return current_len
            return current_len + self.data.height

        if self.data is not None:
            current_len += self.data.height

        for branch in self.branches:
            current_len = branch.len(current_len)

        return current_len

    def divide(self) -> None:
        """Divide the QuadTree"""
        self.northwest = PolarsQuadTree(
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
        self.northeast = PolarsQuadTree(
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
        self.southwest = PolarsQuadTree(
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
        self.southeast = PolarsQuadTree(
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
        self.branches: List[PolarsQuadTree] = [
            self.northwest,
            self.northeast,
            self.southwest,
            self.southeast,
        ]
        self.redistribute_to_branches()

    def _partition_data_wrapped(
        self,
        data: pl.DataFrame,
    ) -> Dict[Tuple[int,], pl.DataFrame]:
        mid_lat = self.boundary.lat
        mid_lon = self.boundary.lon

        res = data.with_columns(pl.col("lat").gt(mid_lat).alias("_cond_gt_lat"))
        if self.boundary.east > mid_lon:
            res = res.with_columns(
                pl.col("lon")
                .is_between(mid_lon, self.boundary.east, closed="right")
                .alias("_cond_gt_lon")
            )
        else:
            res = res.with_columns(
                pl.col("lon")
                .is_between(self.boundary.west, mid_lon, closed="right")
                .alias("_cond_gt_lon")
            )
        res = res.with_columns(
            (pl.col("_cond_gt_lon") + 2 * ~pl.col("_cond_gt_lat")).alias(
                "_cond"
            )
        ).drop("_cond_gt_lon", "_cond_gt_lat")
        return res.partition_by("_cond", as_dict=True)

    def _partition_data(
        self,
        data: pl.DataFrame,
    ) -> Dict[Tuple[int,], pl.DataFrame]:
        if self.boundary.wraps:
            return self._partition_data_wrapped(data=data)
        mid_lat = self.boundary.lat
        mid_lon = self.boundary.lon

        # Order is NW, NE, SW, SE
        # Make bit value:
        # 0 (00) is NW, 1 (01) is NE, 2 (10) is SW, 3 (11) is SE
        res = (
            data.with_columns(
                (pl.col("lon").gt(mid_lon)).alias("_cond_gt_lon"),
                (pl.col("lat").gt(mid_lat)).alias("_cond_gt_lat"),
            )
            .with_columns(
                (pl.col("_cond_gt_lon") + 2 * ~pl.col("_cond_gt_lat")).alias(
                    "_cond"
                )
            )
            .drop("_cond_gt_lon", "_cond_gt_lat")
        )
        return res.partition_by("_cond", as_dict=True)

    def redistribute_to_branches(self) -> bool:
        """Redistribute all points to branches"""
        if not self.divided:
            self.divide()
        if self.data is None or self.data.height == 0:
            return False
        data_sp = self._partition_data(self.data)
        for i, frame in data_sp.items():
            index = int(i[0])
            self.branches[index].insert(frame.drop("_cond", strict=False))
        self.data = None
        return True

    def insert_into_branches(self, data: pl.DataFrame) -> None:
        """Redistribute all points to branches"""
        if not self.divided:
            self.divide()
        data_sp = self._partition_data(data)
        for i, frame in data_sp.items():
            index = int(i[0])
            self.branches[index].insert(frame.drop("_cond", strict=False))
        return None

    def _check_bounds(
        self,
        data: Optional[pl.DataFrame] = None,
        rectangle: Optional[Rectangle] = None,
    ) -> pl.Series:
        if rectangle is None:
            rectangle = self.boundary
        if data is None:
            data = self.data
        if data is None:
            raise ValueError(
                "No Data was passed, could not compare to rectangle"
            )

        return rectangle.check_frame(data)

    def _check_valid(
        self, data: pl.DataFrame
    ) -> Tuple[pl.DataFrame, pl.DataFrame]:
        """
        Returns frame with records in boundary, frame with records outside
        boundary.
        """
        if not all(c in data.columns for c in ["uid", "lat", "lon"]):
            raise ValueError("Require all 'uid', 'lat' and 'lon' columns.")

        data = data.cast(_MIN_SCHEMA, strict=True)

        data = data.with_columns(
            pl.col("lon").alias("_olon"),
            (((pl.col("lon") + 540) % 360) - 180).alias("lon"),
        )
        valid = self._check_bounds(data=data)
        return data.filter(valid), data.remove(valid)

    def query(
        self,
        rect: Rectangle,
        frame: Optional[pl.DataFrame] = None,
    ) -> pl.DataFrame:
        """Query with a rectangle"""
        if frame is None:
            frame = pl.DataFrame(schema=_MIN_SCHEMA)

        if not self.boundary.intersects(rect):
            return frame

        if self.data is not None:
            in_rect = rect.check_frame(self.data)
            frame = pl.concat(
                [frame, self.data.filter(in_rect)], how="diagonal"
            )

        if self.divided:
            for branch in self.branches:
                frame = branch.query(rect, frame=frame)

        return frame

    def query_ellipse(
        self,
        ellipse: Ellipse,
        frame: Optional[pl.DataFrame] = None,
    ) -> pl.DataFrame:
        """Query the Tree with an Ellipse"""
        # TODO: Get this working
        raise NotImplementedError(
            "Querying a PolarsQuadTree with an Ellipse is not yet implemented."
        )

    def nearby_points(
        self,
        lat: float,
        lon: float,
        dist: float,
        frame: Optional[pl.DataFrame] = None,
    ) -> pl.DataFrame:
        """Query with a distance"""
        lon = ((540 + lon) % 360) - 180
        if frame is None:
            frame = pl.DataFrame(schema=_MIN_SCHEMA)

        if not self.boundary.nearby(Record(lat=lat, lon=lon), dist):
            return frame

        if self.data is None and not self.divided:
            return frame

        if self.data is not None:
            candidates = haversine_polars(self.data, lat=lat, lon=lon)
            candidates = candidates.filter(pl.col("_dist").le(dist))

            if candidates.height > 0:
                frame = pl.concat([frame, candidates], how="diagonal")

        if self.divided:
            for branch in self.branches:
                frame = branch.nearby_points(
                    lat=lat,
                    lon=lon,
                    dist=dist,
                    frame=frame,
                )

        return frame

    def insert(self, data: pl.DataFrame, strict: bool = False) -> bool:
        """
        Insert a point into the QuadTree.

        Parameters
        ----------
        data : polars.DataFrame
            The data to insert

        Returns
        -------
        bool
            True if the point was inserted into the QuadTree
        """
        if self.depth == 0:
            # Don't need to do this for lower levels, as this validation
            # automatically propagates (unless this is called directly for a
            # branch...)
            data, bad = self._check_valid(data)
            msg = (
                f"Have {bad.height} rows of data that cannot be inserted, "
                + "outside boundary."
            )
            if bad.height > 0:
                if strict:
                    raise ValueError(msg)
                # Raise?
                warn(msg)

        if data.height == 0:
            return False

        if self.divided:
            self.insert_into_branches(data)
            return True

        self.data = data if self.data is None else pl.concat([self.data, data])

        if self.max_depth and self.depth == self.max_depth:
            return True

        if self.data.height > self.capacity:
            self.divide()

        return True

    def remove(self, uid: str, lat: float, lon: float) -> bool:
        """Remove a value from the Tree"""
        lon = ((540 + lon) % 360) - 180
        r = Record(lon=lon, lat=lat)
        if not self.boundary.contains(r):
            return False
        if self.data is not None:
            uids_have = self.data.get_column("uid")
            if uid in uids_have:
                self.data = self.data.remove(uid=uid)
                return True
        if self.divided:
            for branch in self.branches:
                if branch.remove(uid, lat, lon):
                    return True

        return False
