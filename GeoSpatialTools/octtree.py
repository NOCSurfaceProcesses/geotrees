"""
OctTree
-------
Constuctors for OctTree classes that can decrease the number of comparisons
for detecting nearby records for example. This is an implementation that uses
Haversine distances for comparisons between records for identification of
neighbours.
"""

from dataclasses import dataclass
from typing import List, Optional
import datetime
from .distance_metrics import haversine, destination
from .utils import LatitudeError, DateWarning
from math import degrees, sqrt
from warnings import warn


class SpaceTimeRecord:
    """
    ICOADS Record class.

    This is a simple instance of an ICOARDS record, it requires position and
    temporal data. It can optionally include a UID and extra data.

    The temporal component was designed to use `datetime` values, however all
    methods will work with numeric datetime information - for example a pentad,
    timestamp, julian day, etc. Note that any uses within an OctTree and
    SpaceTimeRectangle must also have timedelta values replaced with numeric
    ranges in this case.

    Equality is checked only on the required fields + UID if it is specified.

    Parameters
    ----------
    lon : float
        Horizontal coordinate (longitude).
    lat : float
        Vertical coordinate (latitude).
    datetime : datetime.datetime
        Datetime of the record. Can also be a numeric value such as pentad.
        Comparisons between Records with datetime and Records with numeric
        datetime will fail.
    uid : str | None
        Unique Identifier.
    fix_lon : bool
        Force longitude to -180, 180
    **data
        Additional data passed to the SpaceTimeRecord for use by other functions
        or classes.
    """

    def __init__(
        self,
        lon: float,
        lat: float,
        datetime: datetime.datetime,
        uid: Optional[str] = None,
        fix_lon: bool = True,
        **data,
    ) -> None:
        self.lon = lon
        if fix_lon:
            # Move lon to -180, 180
            self.lon = ((self.lon + 540) % 360) - 180
        if lat < -90 or lat > 90:
            raise LatitudeError(
                "Expected latitude value to be between -90 and 90 degrees"
            )
        self.lat = lat
        self.datetime = datetime
        self.uid = uid
        for var, val in data.items():
            setattr(self, var, val)
        return None

    def __str__(self) -> str:
        return (
            f"SpaceTimeRecord(x = {self.lon}, y = {self.lat}, "
            + f"datetime = {self.datetime}, uid = {self.uid})"
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SpaceTimeRecord):
            return False
        if self.uid and other.uid:
            return self.uid == other.uid
        return (
            self.lon == other.lon
            and self.lat == other.lat
            and self.datetime == other.datetime
            and (not (self.uid or other.uid) or self.uid == other.uid)
        )

    def distance(self, other: object) -> float:
        """
        Compute the Haversine distance to another SpaceTimeRecord.
        Only computes spatial distance.
        """
        if not isinstance(other, SpaceTimeRecord):
            raise TypeError("Argument other must be an instance of Record")
        return haversine(self.lon, self.lat, other.lon, other.lat)


class SpaceTimeRecords(List[SpaceTimeRecord]):
    """List of SpaceTimeRecords"""


@dataclass
class SpaceTimeRectangle:
    """
    A simple Space Time SpaceTimeRectangle class.

    This constructs a simple Rectangle object.
    The defining coordinates are the centres of the box, and the extents
    are the full width, height, and time extent.

    Whilst the rectangle is assumed to lie on the surface of Earth, this is
    a projection as the rectangle is defined by a longitude/latitude range.

    The temporal components are defined in the same way as the spatial
    components, that is that the `datetime` component (t) is the "centre", and
    the time extent (dt) is the full time range of the box.

    Parameters
    ----------
    west : float
        Western boundary of the Rectangle
    east : float
        Eastern boundary of the Rectangle
    south : float
        Southern boundary of the Rectangle
    north : float
        Northern boundary of the Rectangle
    start : datetime.datetime
        Start datetime of the Rectangle
    end : datetime.datetime
        End datetime of the Rectangle
    """

    west: float
    east: float
    south: float
    north: float
    start: datetime.datetime
    end: datetime.datetime

    def __post_init__(self):
        if self.east > 180 or self.east < -180:
            self.east = ((self.east + 540) % 360) - 180
        if self.west > 180 or self.west < -180:
            self.west = ((self.west + 540) % 360) - 180
        if self.north > 90 or self.south < -90:
            raise LatitudeError(
                "Latitude bounds are out of bounds. "
                + f"{self.north = }, {self.south = }"
            )
        if self.end < self.start:
            warn("End date is before start date. Swapping", DateWarning)
            self.start, self.end = self.end, self.start

    @property
    def lat_range(self) -> float:
        """Latitude range of the Rectangle"""
        return self.north - self.south

    @property
    def lat(self) -> float:
        """Centre latitude of the Rectangle"""
        return self.south + self.lat_range / 2

    @property
    def lon_range(self) -> float:
        """Longitude range of the Rectangle"""
        if self.east < self.west:
            return self.east - self.west + 360

        return self.east - self.west

    @property
    def lon(self) -> float:
        """Centre longitude of the Rectangle"""
        lon = self.west + self.lon_range / 2
        return ((lon + 540) % 360) - 180

    @property
    def edge_dist(self) -> float:
        """Approximate maximum distance from the centre to an edge"""
        corner_dist = max(
            haversine(self.lon, self.lat, self.east, self.north),
            haversine(self.lon, self.lat, self.east, self.south),
        )
        if self.north * self.south < 0:
            corner_dist = max(
                corner_dist,
                haversine(self.lon, self.lat, self.east, 0),
            )
        return corner_dist

    @property
    def time_range(self) -> datetime.timedelta:
        """The time extent of the Rectangle"""
        return self.end - self.start

    @property
    def centre_datetime(self) -> datetime.datetime:
        """The midpoint time of the Rectangle"""
        return self.start + (self.end - self.start) / 2

    def _test_east_west(self, lon: float) -> bool:
        if self.lon_range >= 360:
            # Rectangle encircles earth
            return True
        if self.east > self.lon and self.west < self.lon:
            return lon <= self.east and lon >= self.west
        if self.east < self.lon:
            return not (lon > self.east and lon < self.west)
        if self.west > self.lon:
            return not (lon < self.east and lon > self.west)
        return False

    def _test_north_south(self, lat: float) -> bool:
        return lat <= self.north and lat >= self.south

    def contains(self, point: SpaceTimeRecord) -> bool:
        """Test if a point is contained within the SpaceTimeRectangle"""
        if point.datetime > self.end or point.datetime < self.start:
            return False
        return self._test_north_south(point.lat) and self._test_east_west(
            point.lon
        )

    def intersects(self, other: object) -> bool:
        """Test if another Rectangle object intersects this Rectangle"""
        if not isinstance(other, SpaceTimeRectangle):
            raise TypeError(
                f"other must be a Rectangle class, got {type(other)}"
            )
        if other.end < self.start or other.start > self.end:
            # Not in the same time range
            return False
        if other.south > self.north:
            # Other is fully north of self
            return False
        if other.north < self.south:
            # Other is fully south of self
            return False
        # Handle east / west edges
        return (
            self._test_east_west(other.west)
            or self._test_east_west(other.east)
            # Fully contained within other
            or (
                other._test_east_west(self.west)
                and other._test_east_west(self.east)
            )
        )

    def nearby(
        self,
        point: SpaceTimeRecord,
        dist: float,
        t_dist: datetime.timedelta,
    ) -> bool:
        """
        Check if point is nearby the Rectangle

        Determines if a SpaceTimeRecord that falls on the surface of Earth is
        nearby to the rectangle in space and time. This calculation uses the
        Haversine distance metric.

        Distance from rectangle to point is challenging on the surface of a
        sphere, this calculation will return false positives as a check based
        on the distance from the centre of the rectangle to the corners, or
        to its Eastern edge (if the rectangle crosses the equator) is used in
        combination with the input distance.

        The primary use-case of this method is for querying an OctTree for
        nearby Records.

        Parameters
        ----------
        point : SpaceTimeRecord
        dist : float,
        t_dist : datetime.timedelta

        Returns
        -------
        bool : True if the point is <= dist + max(dist(centre, corners))
        """
        if (
            point.datetime - t_dist > self.end
            or point.datetime + t_dist < self.start
        ):
            return False
        # QUESTION: Is this sufficient? Possibly it is overkill
        return (
            haversine(self.lon, self.lat, point.lon, point.lat)
            <= dist + self.edge_dist
        )


class SpaceTimeEllipse:
    """
    A simple Ellipse Class for an ellipse on the surface of a sphere.

    Parameters
    ----------
    lon : float
        Horizontal centre of the ellipse
    lat : float
        Vertical centre of the ellipse
    a : float
        Length of the semi-major axis
    b : float
        Length of the semi-minor axis
    theta : float
        Angle of the semi-major axis from horizontal anti-clockwise in radians
    start : datetime.datetime
        Start date of the Ellipse
    end : datetime.datetime
        Send date of the Ellipse
    """

    def __init__(
        self,
        lon: float,
        lat: float,
        a: float,
        b: float,
        theta: float,
        start: datetime.datetime,
        end: datetime.datetime,
    ) -> None:
        self.a = a
        self.b = b
        self.lon = lon
        if self.lon > 180:
            self.lon = ((self.lon + 540) % 360) - 180
        self.lat = lat
        self.start = start
        self.end = end

        if self.end < self.start:
            warn("End date is before start date. Swapping")
            self.start, self.end = self.end, self.start
        # theta is anti-clockwise angle from horizontal in radians
        self.theta = theta
        # bearing is angle clockwise from north in degrees
        self.bearing = (90 - degrees(self.theta)) % 360

        a2 = self.a * self.a
        b2 = self.b * self.b

        self.c = sqrt(a2 - b2)
        self.p1_lon, self.p1_lat = destination(
            self.lon,
            self.lat,
            self.bearing,
            self.c,
        )
        self.p2_lon, self.p2_lat = destination(
            self.lon,
            self.lat,
            (self.bearing - 180) % 360,
            self.c,
        )

    def contains(self, point: SpaceTimeRecord) -> bool:
        """Test if a point is contained within the Ellipse"""
        if point.datetime > self.end or point.datetime < self.start:
            return False
        return (
            haversine(self.p1_lon, self.p1_lat, point.lon, point.lat)
            + haversine(self.p2_lon, self.p2_lat, point.lon, point.lat)
        ) <= 2 * self.a

    def nearby_rect(self, rect: SpaceTimeRectangle) -> bool:
        """Test if a rectangle is near to the Ellipse"""
        if rect.start > self.end or rect.end < self.start:
            return False
        # TODO: Check corners, and 0 lat
        return (
            haversine(self.p1_lon, self.p1_lat, rect.lon, rect.lat)
            <= rect.edge_dist + self.a
            and haversine(self.p2_lon, self.p2_lat, rect.lon, rect.lat)
            <= rect.edge_dist + self.a
        )


class OctTree:
    """
    A Simple OctTree class for PyCOADS.

    Acts as a space-time OctTree on the surface of Earth, allowing for querying
    nearby points faster than searching a full DataFrame. As SpaceTimeRecords
    are added to the OctTree, the OctTree divides into 8 children as the
    capacity is reached. Additional SpaceTimeRecords are then added to the
    children where they fall within the child OctTree's boundary.

    SpaceTimeRecords already part of the OctTree before divided are not
    distributed to the children OctTrees.

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
        self.points = SpaceTimeRecords()
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
            out += f"{indent}- with children:\n"
            out += f"{self.northwestback}"
            out += f"{self.northeastback}"
            out += f"{self.southwestback}"
            out += f"{self.southeastback}"
            out += f"{self.northwestfwd}"
            out += f"{self.northeastfwd}"
            out += f"{self.southwestfwd}"
            out += f"{self.southeastfwd}"
        return out

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

    def insert(self, point: SpaceTimeRecord) -> bool:  # noqa: C901
        """
        Insert a SpaceTimeRecord into the QuadTree.

        Note that the SpaceTimeRecord can have numeric datetime values if that
        is consistent with the OctTree.
        """
        if not self.boundary.contains(point):
            return False
        elif self.max_depth and self.depth == self.max_depth:
            self.points.append(point)
            return True
        elif len(self.points) < self.capacity:
            self.points.append(point)
            return True
        else:
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

    def remove(self, point: SpaceTimeRecord) -> bool:  # noqa: C901
        """
        Remove a SpaceTimeRecord from the OctTree if it is in the OctTree.

        Returns True if the SpaceTimeRecord is removed.
        """
        if not self.boundary.contains(point):
            return False

        if point in self.points:
            self.points.remove(point)
            return True

        if not self.divided:
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
        points: Optional[SpaceTimeRecords] = None,
    ) -> SpaceTimeRecords:
        """Get points that fall in a SpaceTimeRectangle"""
        if not points:
            points = SpaceTimeRecords()
        if not self.boundary.intersects(rect):
            return points

        for point in self.points:
            if rect.contains(point):
                points.append(point)

        if self.divided:
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
        points: Optional[SpaceTimeRecords] = None,
    ) -> SpaceTimeRecords:
        """Get points that fall in an ellipse."""
        if not points:
            points = SpaceTimeRecords()
        if not ellipse.nearby_rect(self.boundary):
            return points

        for point in self.points:
            if ellipse.contains(point):
                points.append(point)

        if self.divided:
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
        points: Optional[SpaceTimeRecords] = None,
    ) -> SpaceTimeRecords:
        """
        Get all points that are nearby another point.

        Query the OctTree to find all SpaceTimeRecords within the OctTree that
        are nearby to the query SpaceTimeRecord. This search should be faster
        than searching through all records, since only OctTree children whose
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
        points : SpaceTimeRecords | None
            List of SpaceTimeRecords already found. Most use cases will be to
            not set this value, since it's main use is for passing onto the
            children OctTrees.

        Returns
        -------
        SpaceTimeRecords : A list of SpaceTimeRecords whose distance to the
        query SpaceTimeRecord is <= dist, and the datetimes of the
        SpaceTimeRecords fall within the datetime range of the query
        SpaceTimeRecord.
        """
        if not points:
            points = SpaceTimeRecords()
        if not self.boundary.nearby(point, dist, t_dist):
            return points

        for test_point in self.points:
            if (
                haversine(point.lon, point.lat, test_point.lon, test_point.lat)
                <= dist
                and test_point.datetime <= point.datetime + t_dist
                and test_point.datetime >= point.datetime - t_dist
            ):
                points.append(test_point)

        if self.divided:
            points = self.northwestback.nearby_points(
                point, dist, t_dist, points
            )
            points = self.northeastback.nearby_points(
                point, dist, t_dist, points
            )
            points = self.southwestback.nearby_points(
                point, dist, t_dist, points
            )
            points = self.southeastback.nearby_points(
                point, dist, t_dist, points
            )
            points = self.northwestfwd.nearby_points(
                point, dist, t_dist, points
            )
            points = self.northeastfwd.nearby_points(
                point, dist, t_dist, points
            )
            points = self.southwestfwd.nearby_points(
                point, dist, t_dist, points
            )
            points = self.southeastfwd.nearby_points(
                point, dist, t_dist, points
            )

        return points
