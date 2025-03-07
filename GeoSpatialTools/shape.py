"""
Shape objects for defining QuadTree or OctTree classes, or for defining a query
region for QuadTree and OctTree classes.

Distances between shapes, or between shapes and Records uses the Haversine
distance.

All shape objects account for spherical geometry and the wrapping of longitude
at -180, 180 degrees.

Classes prefixed by "SpaceTime" include a temporal dimension and should be used
with OctTree classes.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from math import degrees, sqrt
from warnings import warn

from .distance_metrics import destination, haversine
from .utils import DateWarning, LatitudeError
from .record import Record, SpaceTimeRecord


@dataclass
class Rectangle:
    """
    A simple Rectangle class

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
    """

    west: float
    east: float
    south: float
    north: float

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

    def contains(self, point: Record) -> bool:
        """Test if a point is contained within the Rectangle"""
        return self._test_north_south(point.lat) and self._test_east_west(
            point.lon
        )

    def intersects(self, other: object) -> bool:
        """Test if another Rectangle object intersects this Rectangle"""
        if not isinstance(other, Rectangle):
            raise TypeError(
                f"other must be a Rectangle class, got {type(other)}"
            )
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
        point: Record,
        dist: float,
    ) -> bool:
        """Check if point is nearby the Rectangle"""
        # QUESTION: Is this sufficient? Possibly it is overkill
        return (
            haversine(self.lon, self.lat, point.lon, point.lat)
            <= dist + self.edge_dist
        )


class Ellipse:
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
    """

    def __init__(
        self,
        lon: float,
        lat: float,
        a: float,
        b: float,
        theta: float,
    ) -> None:
        self.a = a
        self.b = b
        self.lon = lon
        if self.lon > 180:
            self.lon = ((self.lon + 540) % 360) - 180
        self.lat = lat
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

    def contains(self, point: Record) -> bool:
        """Test if a point is contained within the Ellipse"""
        return (
            haversine(self.p1_lon, self.p1_lat, point.lon, point.lat)
            + haversine(self.p2_lon, self.p2_lat, point.lon, point.lat)
        ) <= 2 * self.a

    def nearby_rect(self, rect: Rectangle) -> bool:
        """Test if a rectangle is near to the Ellipse"""
        return (
            haversine(self.p1_lon, self.p1_lat, rect.lon, rect.lat)
            <= rect.edge_dist + self.a
            and haversine(self.p2_lon, self.p2_lat, rect.lon, rect.lat)
            <= rect.edge_dist + self.a
        )


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
    start: datetime
    end: datetime

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
    def time_range(self) -> timedelta:
        """The time extent of the Rectangle"""
        return self.end - self.start

    @property
    def centre_datetime(self) -> datetime:
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
        t_dist: timedelta,
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
        start: datetime,
        end: datetime,
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
