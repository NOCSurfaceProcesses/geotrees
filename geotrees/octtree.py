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
Constructors for OctTree classes that can decrease the number of comparisons
for detecting nearby records for example. This is an implementation that uses
Haversine distances for comparisons between records for identification of
neighbours.
"""

import datetime
from typing import Dict, List, Optional, Tuple
from warnings import warn

import polars as pl

from geotrees.distance_metrics import haversine_polars
from geotrees.record import SpaceTimeRecord
from geotrees.shape import SpaceTimeEllipse, SpaceTimeRectangle
from geotrees.utils import FailedInsertWarning


_MIN_SCHEMA = pl.Schema(
    {
        "uid": pl.String,
        "lat": pl.Float64,
        "lon": pl.Float64,
        "datetime": pl.Datetime("us"),
    }
)


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
        The bounding SpaceTimeRectangle of the OctTree
    capacity : int
        The capacity of each cell, if max_depth is set then a cell at the
        maximum depth may contain more points than the capacity.
    depth : int
        The current depth of the cell. Initialises to zero if unset.
    max_depth : int | None
        The maximum depth of the OctTree. If set, this can override the
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
        """Divide the OctTree"""
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
        self.branches: list[OctTree] = [
            self.northwestback,
            self.northeastback,
            self.southwestback,
            self.southeastback,
            self.northwestfwd,
            self.northeastfwd,
            self.southwestfwd,
            self.southeastfwd,
        ]
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

    def remove(self, point: SpaceTimeRecord) -> bool:
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

        for branch in self.branches:
            if branch.remove(point):
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

        for branch in self.branches:
            points = branch.query(rect, points)

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

        for branch in self.branches:
            points = branch.query_ellipse(ellipse, points)

        return points

    def nearby_points(
        self,
        point: SpaceTimeRecord,
        dist: float,
        t_dist: datetime.timedelta,
        points: Optional[List[SpaceTimeRecord]] = None,
        exclude_self: bool = False,
        min_dist: float = 0.0,
    ) -> List[SpaceTimeRecord]:
        """
        Get all SpaceTimeRecords contained in the OctTree that are nearby
        another query SpaceTimeRecord.

        Query the OctTree to find all SpaceTimeRecords within the OctTree that
        are nearby to the query SpaceTimeRecord. This search should be faster
        than searching through all records, since only OctTree branch whose
        boundaries are close to the query SpaceTimeRecord are evaluated.

        A 'dist' attribute is added to the resulting SpaceTimeRecords, for
        convenience, saving re-computation as a later step.

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
        min_dist : float
            Minimum spatial distance used in comparison. Any points with
            distance less than this value will not be returned. Defaults to 0.0.


        Returns
        -------
        list[SpaceTimeRecord]
            A list of SpaceTimeRecords whose distance to the
            query SpaceTimeRecord is between min_dist and dist, and the
            datetimes of the SpaceTimeRecords fall within the datetime range of
            the query SpaceTimeRecord.
        """
        if not points:
            points = list()
        if not self.boundary.nearby(point, dist, t_dist):
            return points

        # Points are only in leaf nodes
        if not self.divided:
            for test_point in self.points:
                test_distance = test_point.distance(point)
                if (
                    min_dist <= test_distance <= dist
                    and test_point.datetime <= point.datetime + t_dist
                    and test_point.datetime >= point.datetime - t_dist
                ):
                    if exclude_self and point == test_point:
                        continue
                    setattr(test_point, "dist", test_distance)
                    points.append(test_point)
            return points

        for branch in self.branches:
            points = branch.nearby_points(
                point,
                dist=dist,
                t_dist=t_dist,
                points=points,
                exclude_self=exclude_self,
                min_dist=min_dist,
            )

        return points


class PolarsOctTree:
    """Polars version of OctTree"""

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
        out = f"{indent}OctTree:\n"
        out += f"{indent}- boundary: {self.boundary}\n"
        out += f"{indent}- capacity: {self.capacity}\n"
        out += f"{indent}- depth: {self.depth}\n"
        if self.max_depth:
            out += f"{indent}- max_depth: {self.max_depth}\n"
        if self.data is not None:
            out += f"{indent}- contents:\n"
            out += f"{indent}- number of elements: {self.data.height}\n"
            out += f"{indent}- {self.data}\n"
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

    def divide(self):
        """Divide the OctTree"""
        self.northwestfwd = PolarsOctTree(
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
        self.northeastfwd = PolarsOctTree(
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
        self.southwestfwd = PolarsOctTree(
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
        self.southeastfwd = PolarsOctTree(
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
        self.northwestback = PolarsOctTree(
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
        self.northeastback = PolarsOctTree(
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
        self.southwestback = PolarsOctTree(
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
        self.southeastback = PolarsOctTree(
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
        self.branches: list[PolarsOctTree] = [
            self.northwestback,
            self.northeastback,
            self.southwestback,
            self.southeastback,
            self.northwestfwd,
            self.northeastfwd,
            self.southwestfwd,
            self.southeastfwd,
        ]
        self.redistribute_to_branches()

    def _partition_data_wrapped(
        self,
        data: pl.DataFrame,
    ) -> Dict[Tuple[int,], pl.DataFrame]:
        mid_lat = self.boundary.lat
        mid_lon = self.boundary.lon
        mid_date = self.boundary.centre_datetime

        res = data.with_columns(
            pl.col("lat").ge(mid_lat).alias("_cond_gt_lat"),
            pl.col("datetime").gt(mid_date).alias("_cond_gt_dt"),
        )
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
        # Order is NW, NE, SW, SE, BCK, FWD
        # Make bit value:
        # 0 (000) is NWB, 1 (001) is NEB, 2 (010) is SWB, 3 (011) is SEB
        # 4 (100) is NWF, 5 (101) is NEF, 6 (110) is SWF, 7 (111) is SEF
        res = res.with_columns(
            (
                pl.col("_cond_gt_lon")
                + 2 * ~pl.col("_cond_gt_lat")
                + 4 * pl.col("_cond_gt_dt")
            ).alias("_cond")
        ).drop("_cond_gt_lon", "_cond_gt_lat", "_cond_gt_dt")
        return res.partition_by("_cond", as_dict=True)

    def _partition_data(
        self,
        data: pl.DataFrame,
    ) -> Dict[Tuple[int,], pl.DataFrame]:
        if self.boundary.wraps:
            return self._partition_data_wrapped(data=data)
        mid_lat = self.boundary.lat
        mid_lon = self.boundary.lon
        mid_date = self.boundary.centre_datetime

        # Order is NW, NE, SW, SE, BCK, FWD
        # Make bit value:
        # 0 (000) is NWB, 1 (001) is NEB, 2 (010) is SWB, 3 (011) is SEB
        # 4 (100) is NWF, 5 (101) is NEF, 6 (110) is SWF, 7 (111) is SEF
        res = (
            data.with_columns(
                (pl.col("lon").gt(mid_lon)).alias("_cond_gt_lon"),
                (pl.col("lat").ge(mid_lat)).alias("_cond_gt_lat"),
                pl.col("datetime").gt(mid_date).alias("_cond_gt_dt"),
            )
            .with_columns(
                (
                    pl.col("_cond_gt_lon")
                    + 2 * ~pl.col("_cond_gt_lat")
                    + 4 * pl.col("_cond_gt_dt")
                ).alias("_cond")
            )
            .drop("_cond_gt_lon", "_cond_gt_lat", "_cond_gt_dt")
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
        rectangle: Optional[SpaceTimeRectangle] = None,
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
        rect: SpaceTimeRectangle,
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
        ellipse: SpaceTimeEllipse,
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
        datetime: datetime.datetime,
        dist: float,
        t_dist: datetime.timedelta,
        frame: Optional[pl.DataFrame] = None,
    ) -> pl.DataFrame:
        """Query with a distance"""
        lon = ((540 + lon) % 360) - 180
        if frame is None:
            frame = pl.DataFrame(schema=_MIN_SCHEMA)

        if not self.boundary.nearby(
            SpaceTimeRecord(lat=lat, lon=lon, datetime=datetime),
            dist=dist,
            t_dist=t_dist,
        ):
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
                    datetime=datetime,
                    dist=dist,
                    frame=frame,
                    t_dist=t_dist,
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
                warn(msg, FailedInsertWarning)

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

    def remove(
        self, uid: str, lat: float, lon: float, datetime: datetime.datetime
    ) -> bool:
        """Remove a value from the Tree"""
        lon = ((540 + lon) % 360) - 180
        r = SpaceTimeRecord(lon=lon, lat=lat, datetime=datetime)
        if not self.boundary.contains(r):
            return False
        if self.data is not None:
            uids_have = self.data.get_column("uid")
            if uid in uids_have:
                self.data = self.data.remove(uid=uid)
                return True
        if self.divided:
            for branch in self.branches:
                if branch.remove(uid, lat, lon, datetime):
                    return True

        return False
