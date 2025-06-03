"""
Record objects used for containing data passed to QuadTree, OctTree and KDTree
classes. Require positions defined by "lon" and "lat", SpaceTimeRecord objects
also require "datetime". Optional fields are "uid", other data can be passed as
keyword arguments. Only positional, temporal, and uid values are used for
equality checks.

Distances between records is calculated using Haversine distance.

Classes prefixed by "SpaceTime" include a temporal dimension and should be used
with OctTree classes.
"""

from datetime import datetime
from typing import Optional

from geotrees.distance_metrics import haversine
from geotrees.utils import LatitudeError


class Record:
    """
    A simple instance of a record, it requires position data. It can optionally
    include datetime, a UID, and extra data passed as keyword arguments.

    Equality is first checked on uid values, if both Records have a uid value
    then the Records are equal if the uids are equal. Otherwise records are
    compared by checking only on the required fields & uid if it is specified.

    By default, longitudes are converted to -180, 180 for consistency. This
    behaviour can be toggled by setting `fix_lon` to False.

    Passing additional fields is possible as keyword arguments. For example SST
    values can be added to the Record. This could be useful for buddy checking
    for example where one would compare SST against neighbour values.

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
        return (
            f"Record(lon = {self.lon}, lat = {self.lat}, "
            + f"datetime = {self.datetime}, uid = {self.uid})"
        )

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


class SpaceTimeRecord:
    """
    A simple instance of a record object, it requires position and temporal
    data. It can optionally include a UID and extra data.

    The temporal component was designed to use `datetime` values, however all
    methods will work with numeric datetime information - for example a pentad,
    timestamp, julian day, etc. Note that any uses within an OctTree and
    SpaceTimeRectangle must also have timedelta values replaced with numeric
    ranges in this case.

    Equality is first checked on uid values, if both Records have a uid value
    then the Records are equal if the uids are equal. Otherwise records are
    compared by checking only on the required fields & uid if it is specified.

    By default, longitudes are converted to -180, 180 for consistency. This
    behaviour can be toggled by setting `fix_lon` to False.

    Passing additional fields is possible as keyword arguments. For example SST
    values can be added to the Record. This could be useful for buddy checking
    for example where one would compare SST against neighbour values.

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
        datetime: datetime,
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
