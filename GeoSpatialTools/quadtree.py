"""
QuadTree
--------
Constuctors for QuadTree classes that can decrease the number of comparisons
for detecting nearby records for example. This is an implementation that uses
Haversine distances for comparisons between records for identification of
neighbours.
"""

from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime
from .distance_metrics import haversine, destination
from .utils import LatitudeError
from math import degrees, sqrt


class Record:
    """
    ICOADS Record class

    This is a simple instance of an ICOARDS record, it requires position data.
    It can optionally include datetime, a UID, and extra data passed as
    keyword arguments.

    Equality is checked only on the required fields + UID if it is specified.

    Parameters
    ----------
    lon : float
        Horizontal coordinate
    lat : float
        Vertical coordinate
    datetime : datetime | None
        Datetime of the record
    uid : str | None
        Unique Identifier
    fix_lon : bool
        Force longitude to -180, 180
    **data
        Additional data passed to the Record for use by other functions or
        classes.
    """

    def __init__(
        self,
        lon: float,
        lat: float,
        datetime: Optional[datetime] = None,
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
        return f"Record(lon = {self.lon}, lat = {self.lat}, datetime = {self.datetime}, uid = {self.uid})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Record):
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
        """Compute the Haversine distance to another Record"""
        if not isinstance(other, Record):
            raise TypeError("Argument other must be an instance of Record")
        return haversine(self.lon, self.lat, other.lon, other.lat)


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


class QuadTree:
    """
    A Simple QuadTree class for PyCOADS

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
            out += f"{indent}- with children:\n"
            out += f"{self.northwest}"
            out += f"{self.northeast}"
            out += f"{self.southwest}"
            out += f"{self.southeast}"
        return out

    def divide(self):
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

    def insert(self, point: Record) -> bool:
        """Insert a point into the QuadTree"""
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
            if self.northwest.insert(point):
                return True
            elif self.northeast.insert(point):
                return True
            elif self.southwest.insert(point):
                return True
            elif self.southeast.insert(point):
                return True
            return False

    def remove(self, point: Record) -> bool:
        """
        Remove a Record from the QuadTree if it is in the QuadTree.

        Returns True if the Record is removed.
        """
        if not self.boundary.contains(point):
            return False

        if point in self.points:
            self.points.remove(point)
            return True

        if not self.divided:
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
        """Get points that fall in a rectangle"""
        if not points:
            points = list()
        if not self.boundary.intersects(rect):
            return points

        for point in self.points:
            if rect.contains(point):
                points.append(point)

        if self.divided:
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
        """Get points that fall in an ellipse."""
        if not points:
            points = list()
        if not ellipse.nearby_rect(self.boundary):
            return points

        for point in self.points:
            if ellipse.contains(point):
                points.append(point)

        if self.divided:
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
    ) -> List[Record]:
        """Get all points that are nearby another point"""
        if not points:
            points = list()
        if not self.boundary.nearby(point, dist):
            return points

        for test_point in self.points:
            if (
                haversine(point.lon, point.lat, test_point.lon, test_point.lat)
                <= dist
            ):
                points.append(test_point)

        if self.divided:
            points = self.northwest.nearby_points(point, dist, points)
            points = self.northeast.nearby_points(point, dist, points)
            points = self.southwest.nearby_points(point, dist, points)
            points = self.southeast.nearby_points(point, dist, points)

        return points
