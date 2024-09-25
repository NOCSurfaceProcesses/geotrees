"""
Constuctors for QuadTree classes that can decrease the number of comparisons
for detecting nearby records for example
"""

from datetime import datetime
from .distance_metrics import haversine, destination
from math import degrees, sqrt


class Record:
    """
    ICOADS Record class

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
    """

    def __init__(
        self,
        lon: float,
        lat: float,
        datetime: datetime | None = None,
        uid: str | None = None,
        **data,
    ) -> None:
        self.lon = lon
        self.lat = lat
        self.datetime = datetime
        self.uid = uid
        for var, val in data.items():
            setattr(self, var, val)
        return None

    def __str__(self) -> str:
        return f"Record(x = {self.lon}, y = {self.lat}, datetime = {self.datetime}, uid = {self.uid})"

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, Record)
            and self.lon == other.lon
            and self.lat == other.lat
            and self.datetime == other.datetime
            and (not (self.uid or other.uid) or self.uid == other.uid)
        )


class Rectangle:
    """
    A simple Rectangle class

    Parameters
    ----------
    lon : float
        Horizontal centre of the rectangle
    lat : float
        Vertical centre of the rectangle
    lon_range : float
        Width of the rectangle
    lat_range : float
        Height of the rectangle
    """

    def __init__(
        self,
        lon: float,
        lat: float,
        lon_range: float,
        lat_range: float,
    ) -> None:
        self.lon = lon
        self.lat = lat
        self.lon_range = lon_range
        self.lat_range = lat_range

    def __str__(self) -> str:
        return f"Rectangle(x = {self.lon}, y = {self.lat}, w = {self.lon_range}, h = {self.lat_range})"

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, Rectangle)
            and self.lon == other.lon
            and self.lat == other.lat
            and self.lon_range == other.lon_range
            and self.lat_range == other.lat_range
        )

    def contains(self, point: Record) -> bool:
        """Test if a point is contained within the Rectangle"""
        return (
            point.lon <= self.lon + self.lon_range / 2
            and point.lon >= self.lon - self.lon_range / 2
            and point.lat <= self.lat + self.lat_range / 2
            and point.lat >= self.lat - self.lat_range / 2
        )

    def intersects(self, other: object) -> bool:
        """Test if another Rectangle object intersects this Rectangle"""
        return isinstance(other, Rectangle) and not (
            self.lon - self.lon_range / 2 > other.lon + other.lon_range / 2
            or self.lon + self.lon_range / 2 < other.lon - other.lon_range / 2
            or self.lat - self.lat_range / 2 > other.lat + other.lat_range / 2
            or self.lat + self.lat_range / 2 < other.lat - other.lat_range / 2
        )

    def nearby(
        self,
        point: Record,
        dist: float,
    ) -> bool:
        """Check if point is nearby the Rectangle"""
        # QUESTION: Is this sufficient? Possibly it is overkill
        corner_dist = max(
            haversine(
                self.lon,
                self.lat,
                self.lon + self.lon_range / 2,
                self.lat + self.lat_range / 2,
            ),
            haversine(
                self.lon,
                self.lat,
                self.lon + self.lon_range / 2,
                self.lat - self.lat_range / 2,
            ),
        )
        if (self.lat + self.lat_range / 2) * (
            self.lat - self.lat_range / 2
        ) < 0:
            corner_dist = max(
                corner_dist,
                haversine(self.lon, self.lat, self.lon + self.lon_range / 2, 0),
            )
        return (
            haversine(self.lon, self.lat, point.lon, point.lat)
            <= dist + corner_dist
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
            (180 - self.bearing) % 360,
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
        # TODO: Check corners, and 0 lat
        corner_dist = max(
            haversine(
                rect.lon,
                rect.lat,
                rect.lon + rect.lon_range / 2,
                rect.lat + rect.lat_range / 2,
            ),
            haversine(
                rect.lon,
                rect.lat,
                rect.lon + rect.lon_range / 2,
                rect.lat - rect.lat_range / 2,
            ),
        )
        if (rect.lat + rect.lat_range / 2) * (
            rect.lat - rect.lat_range / 2
        ) < 0:
            corner_dist = max(
                corner_dist,
                haversine(rect.lon, rect.lat, rect.lon + rect.lon_range / 2, 0),
            )
        return (
            haversine(self.p1_lon, self.p1_lat, rect.lon, rect.lat)
            <= corner_dist + self.a
            or haversine(self.p2_lon, self.p2_lat, rect.lon, rect.lat)
            <= corner_dist + self.a
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
        max_depth: int | None = None,
    ) -> None:
        self.boundary = boundary
        self.capacity = capacity
        self.depth = depth
        self.max_depth = max_depth
        self.points: list[Record] = list()
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
                self.boundary.lon - self.boundary.lon_range / 4,
                self.boundary.lat + self.boundary.lat_range / 4,
                self.boundary.lon_range / 2,
                self.boundary.lat_range / 2,
            ),
            capacity=self.capacity,
            depth=self.depth + 1,
            max_depth=self.max_depth,
        )
        self.northeast = QuadTree(
            Rectangle(
                self.boundary.lon + self.boundary.lon_range / 4,
                self.boundary.lat + self.boundary.lat_range / 4,
                self.boundary.lon_range / 2,
                self.boundary.lat_range / 2,
            ),
            capacity=self.capacity,
            depth=self.depth + 1,
            max_depth=self.max_depth,
        )
        self.southwest = QuadTree(
            Rectangle(
                self.boundary.lon - self.boundary.lon_range / 4,
                self.boundary.lat - self.boundary.lat_range / 4,
                self.boundary.lon_range / 2,
                self.boundary.lat_range / 2,
            ),
            capacity=self.capacity,
            depth=self.depth + 1,
            max_depth=self.max_depth,
        )
        self.southeast = QuadTree(
            Rectangle(
                self.boundary.lon + self.boundary.lon_range / 4,
                self.boundary.lat - self.boundary.lat_range / 4,
                self.boundary.lon_range / 2,
                self.boundary.lat_range / 2,
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

    def query(
        self,
        rect: Rectangle,
        points: list[Record] | None = None,
    ) -> list[Record]:
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
        points: list[Record] | None = None,
    ) -> list[Record]:
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
        points: list[Record] | None = None,
    ) -> list[Record]:
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
