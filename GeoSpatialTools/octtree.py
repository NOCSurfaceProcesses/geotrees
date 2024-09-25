from datetime import datetime, timedelta
from .distance_metrics import haversine
from .distance_metrics import haversine, destination
from math import degrees, sqrt


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
    datetime : datetime
        Datetime of the record. Can also be a numeric value such as pentad.
        Comparisons between Records with datetime and Records with numeric
        datetime will fail.
    uid : str | None
        Unique Identifier.
    **data
        Additional data passed to the SpaceTimeRecord for use by other functions
        or classes.
    """

    def __init__(
        self,
        lon: float,
        lat: float,
        datetime: datetime,
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
            isinstance(other, SpaceTimeRecord)
            and self.lon == other.lon
            and self.lat == other.lat
            and self.datetime == other.datetime
            and (not (self.uid or other.uid) or self.uid == other.uid)
        )


class SpaceTimeRecords(list[SpaceTimeRecord]):
    """List of SpaceTimeRecords"""


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
    lon : float
        Horizontal centre of the rectangle (longitude).
    lat : float
        Vertical centre of the rectangle (latitude).
    datetime : datetime
        Datetime centre of the rectangle.
    w : float
        Width of the rectangle (longitude range).
    h : float
        Height of the rectangle (latitude range).
    dt : timedelta
        time extent of the rectangle.
    """

    def __init__(
        self,
        lon: float,
        lat: float,
        datetime: datetime,
        lon_range: float,
        lat_range: float,
        dt: timedelta,
    ) -> None:
        self.lon = lon
        self.lat = lat
        self.lon_range = lon_range
        self.lat_range = lat_range
        self.datetime = datetime
        self.dt = dt

    def __str__(self) -> str:
        return f"SpaceTimeRectangle(x = {self.lon}, y = {self.lat}, w = {self.lon_range}, h = {self.lat_range}, t = {self.datetime}, dt = {self.dt})"

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, SpaceTimeRectangle)
            and self.lon == other.lon
            and self.lat == other.lat
            and self.lon_range == other.lon_range
            and self.lat_range == other.lat_range
            and self.datetime == other.datetime
            and self.dt == other.dt
        )

    def contains(self, point: SpaceTimeRecord) -> bool:
        """Test if a point is contained within the SpaceTimeRectangle"""
        return (
            point.lon <= self.lon + self.lon_range / 2
            and point.lon >= self.lon - self.lon_range / 2
            and point.lat <= self.lat + self.lat_range / 2
            and point.lat >= self.lat - self.lat_range / 2
            and point.datetime <= self.datetime + self.dt / 2
            and point.datetime >= self.datetime - self.dt / 2
        )

    def intersects(self, other: object) -> bool:
        """Test if another Rectangle object intersects this Rectangle"""
        return isinstance(other, SpaceTimeRectangle) and not (
            self.lon - self.lon_range / 2 > other.lon + other.lon_range / 2
            or self.lon + self.lon_range / 2 < other.lon - other.lon_range / 2
            or self.lat - self.lat_range / 2 > other.lat + other.lat_range / 2
            or self.lat + self.lat_range / 2 < other.lat - other.lat_range / 2
            or self.datetime - self.dt / 2 > other.datetime + other.dt / 2
            or self.datetime + self.dt / 2 < other.datetime - other.dt / 2
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
        t_dist : timedelta

        Returns
        -------
        bool : True if the point is <= dist + max(dist(centre, corners))
        """
        if (
            point.datetime - t_dist > self.datetime + self.dt / 2
            or point.datetime + t_dist < self.datetime - self.dt / 2
        ):
            return False
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


class SpaceTimeEllipse:
    """
    A simple Ellipse Class for an ellipse on the surface of a sphere.

    Parameters
    ----------
    lon : float
        Horizontal centre of the ellipse
    lat : float
        Vertical centre of the ellipse
    datetime : datetime
        Datetime centre of the ellipse.
    a : float
        Length of the semi-major axis
    b : float
        Length of the semi-minor axis
    theta : float
        Angle of the semi-major axis from horizontal anti-clockwise in radians
    dt : timedelta
        (full) time extent of the ellipse.
    """

    def __init__(
        self,
        lon: float,
        lat: float,
        datetime: datetime,
        a: float,
        b: float,
        theta: float,
        dt: timedelta,
    ) -> None:
        self.a = a
        self.b = b
        self.lon = lon
        self.lat = lat
        self.datetime = datetime
        self.dt = dt
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

    def contains(self, point: SpaceTimeRecord) -> bool:
        """Test if a point is contained within the Ellipse"""
        return (
            (
                haversine(self.p1_lon, self.p1_lat, point.lon, point.lat)
                + haversine(self.p2_lon, self.p2_lat, point.lon, point.lat)
            )
            <= 2 * self.a
            and point.datetime <= self.datetime + self.dt / 2
            and point.datetime >= self.datetime - self.dt / 2
        )

    def nearby_rect(self, rect: SpaceTimeRectangle) -> bool:
        """Test if a rectangle is near to the Ellipse"""
        if (
            rect.datetime - rect.dt / 2 > self.datetime + self.dt / 2
            or rect.datetime + rect.dt / 2 < self.datetime - self.dt / 2
        ):
            return False
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
            and haversine(self.p2_lon, self.p2_lat, rect.lon, rect.lat)
            <= corner_dist + self.a
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
        max_depth: int | None = None,
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
                self.boundary.lon - self.boundary.lon_range / 4,
                self.boundary.lat + self.boundary.lat_range / 4,
                self.boundary.datetime + self.boundary.dt / 4,
                self.boundary.lon_range / 2,
                self.boundary.lat_range / 2,
                self.boundary.dt / 2,
            ),
            capacity=self.capacity,
            depth=self.depth + 1,
            max_depth=self.max_depth,
        )
        self.northeastfwd = OctTree(
            SpaceTimeRectangle(
                self.boundary.lon + self.boundary.lon_range / 4,
                self.boundary.lat + self.boundary.lat_range / 4,
                self.boundary.datetime + self.boundary.dt / 4,
                self.boundary.lon_range / 2,
                self.boundary.lat_range / 2,
                self.boundary.dt / 2,
            ),
            capacity=self.capacity,
            depth=self.depth + 1,
            max_depth=self.max_depth,
        )
        self.southwestfwd = OctTree(
            SpaceTimeRectangle(
                self.boundary.lon - self.boundary.lon_range / 4,
                self.boundary.lat - self.boundary.lat_range / 4,
                self.boundary.datetime + self.boundary.dt / 4,
                self.boundary.lon_range / 2,
                self.boundary.lat_range / 2,
                self.boundary.dt / 2,
            ),
            capacity=self.capacity,
            depth=self.depth + 1,
            max_depth=self.max_depth,
        )
        self.southeastfwd = OctTree(
            SpaceTimeRectangle(
                self.boundary.lon + self.boundary.lon_range / 4,
                self.boundary.lat - self.boundary.lat_range / 4,
                self.boundary.datetime + self.boundary.dt / 4,
                self.boundary.lon_range / 2,
                self.boundary.lat_range / 2,
                self.boundary.dt / 2,
            ),
            capacity=self.capacity,
            depth=self.depth + 1,
            max_depth=self.max_depth,
        )
        self.northwestback = OctTree(
            SpaceTimeRectangle(
                self.boundary.lon - self.boundary.lon_range / 4,
                self.boundary.lat + self.boundary.lat_range / 4,
                self.boundary.datetime - self.boundary.dt / 4,
                self.boundary.lon_range / 2,
                self.boundary.lat_range / 2,
                self.boundary.dt / 2,
            ),
            capacity=self.capacity,
            depth=self.depth + 1,
            max_depth=self.max_depth,
        )
        self.northeastback = OctTree(
            SpaceTimeRectangle(
                self.boundary.lon + self.boundary.lon_range / 4,
                self.boundary.lat + self.boundary.lat_range / 4,
                self.boundary.datetime - self.boundary.dt / 4,
                self.boundary.lon_range / 2,
                self.boundary.lat_range / 2,
                self.boundary.dt / 2,
            ),
            capacity=self.capacity,
            depth=self.depth + 1,
            max_depth=self.max_depth,
        )
        self.southwestback = OctTree(
            SpaceTimeRectangle(
                self.boundary.lon - self.boundary.lon_range / 4,
                self.boundary.lat - self.boundary.lat_range / 4,
                self.boundary.datetime - self.boundary.dt / 4,
                self.boundary.lon_range / 2,
                self.boundary.lat_range / 2,
                self.boundary.dt / 2,
            ),
            capacity=self.capacity,
            depth=self.depth + 1,
            max_depth=self.max_depth,
        )
        self.southeastback = OctTree(
            SpaceTimeRectangle(
                self.boundary.lon + self.boundary.lon_range / 4,
                self.boundary.lat - self.boundary.lat_range / 4,
                self.boundary.datetime - self.boundary.dt / 4,
                self.boundary.lon_range / 2,
                self.boundary.lat_range / 2,
                self.boundary.dt / 2,
            ),
            capacity=self.capacity,
            depth=self.depth + 1,
            max_depth=self.max_depth,
        )
        self.divided = True

    def _datetime_is_numeric(self) -> bool:
        return not isinstance(self.boundary.datetime, datetime)

    def insert(self, point: SpaceTimeRecord) -> bool:
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

    def query(
        self,
        rect: SpaceTimeRectangle,
        points: SpaceTimeRecords | None = None,
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
        points: SpaceTimeRecords | None = None,
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
        t_dist: timedelta,
        points: SpaceTimeRecords | None = None,
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
        t_dist : timedelta
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
