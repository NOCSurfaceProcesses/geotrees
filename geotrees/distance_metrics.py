"""
Distance Metrics
----------------
Functions for computing navigational information. Can be used to add
navigational information to DataFrames.
"""

from math import acos, asin, atan2, cos, degrees, radians, sin, sqrt
from typing import Tuple


def gcd_slc(
    lon0: float,
    lat0: float,
    lon1: float,
    lat1: float,
) -> float:
    """
    Compute great circle distance on earth surface between two locations.

    Parameters
    ----------
    lon0 : float
        Longitude of position 0
    lat0 : float
        Latitude of position 0
    lon1 : float
        Longitude of position 1
    lat1 : float
        Latitude of position 1

    Returns
    -------
    dist : float
        Great circle distance between position 0 and position 1.

    """
    if abs(lat0 - lat1) <= 1e-6 and abs(lon0 - lon1) <= 1e-6:
        return 0

    r_earth = 6371

    # Convert to radians
    lat0, lat1, lon0, lon1 = map(radians, [lat0, lat1, lon0, lon1])

    return r_earth * acos(
        sin(lat0) * sin(lat1) + cos(lat0) * cos(lat1) * cos(lon1 - lon0)
    )


def haversine(
    lon0: float,
    lat0: float,
    lon1: float,
    lat1: float,
) -> float:
    """
    Compute Haversine distance between two points.

    Parameters
    ----------
    lon0 : float
        Longitude of position 0
    lat0 : float
        Latitude of position 0
    lon1 : float
        Longitude of position 1
    lat1 : float
        Latitude of position 1

    Returns
    -------
    dist : float
        Haversine distance between position 0 and position 1.

    """
    lat0, lat1, dlon, dlat = map(
        radians, [lat0, lat1, lon1 - lon0, lat1 - lat0]
    )
    if abs(dlon) < 1e-6 and abs(dlat) < 1e-6:
        return 0

    r_earth = 6371

    a = sin(dlat / 2) ** 2 + cos(lat0) * cos(lat1) * sin(dlon / 2) ** 2
    c = 2 * asin(sqrt(a))
    return c * r_earth


def bearing(
    lon0: float,
    lat0: float,
    lon1: float,
    lat1: float,
) -> float:
    """
    Compute the bearing of a track from (lon0, lat0) to (lon1, lat1).

    Duplicated from geo-py

    Parameters
    ----------
    lon0 : float,
        Longitude of start point
    lat0 : float,
        Latitude of start point
    lon1 : float,
        Longitude of target point
    lat1 : float,
        Latitude of target point

    Returns
    -------
    bearing : float
        The bearing from point (lon0, lat0) to point (lon1, lat1) in degrees.
    """
    lon0, lat0, lon1, lat1 = map(radians, [lon0, lat0, lon1, lat1])

    dlon = lon1 - lon0
    numerator = sin(dlon) * cos(lat1)
    denominator = cos(lat0) * sin(lat1) - (sin(lat0) * cos(lat1) * cos(dlon))

    theta = atan2(numerator, denominator)
    theta_deg = (degrees(theta) + 360) % 360
    return theta_deg


def destination(
    lon: float, lat: float, bearing: float, distance: float
) -> Tuple[float, float]:
    """
    Compute destination of a great circle path.

    Compute the destination of a track started from 'lon', 'lat', with
    'bearing'. Distance is in units of km.

    Duplicated from geo-py

    Parameters
    ----------
    lon : float
        Longitude of initial position
    lat : float
        Latitude of initial position
    bearing : float
        Direction of track
    distance : float
        Distance to travel

    Returns
    -------
    destination : tuple[float, float]
        Longitude and Latitude of final position
    """
    lon, lat = radians(lon), radians(lat)
    radians_bearing = radians(bearing)
    r_earth = 6371
    delta = distance / r_earth

    lat2 = asin(
        sin(lat) * cos(delta) + cos(lat) * sin(delta) * cos(radians_bearing)
    )
    numerator = sin(radians_bearing) * sin(delta) * cos(lat)
    denominator = cos(delta) - sin(lat) * sin(lat2)

    lon2 = lon + atan2(numerator, denominator)

    lon2_deg = (degrees(lon2) + 540) % 360 - 180
    lat2_deg = degrees(lat2)

    return lon2_deg, lat2_deg


def midpoint(
    lon0: float,
    lat0: float,
    lon1: float,
    lat1: float,
) -> Tuple[float, float]:
    """
    Compute the midpoint of a great circle track

    Parameters
    ----------
    lon0 : float
        Longitude of position 0
    lat0 : float
        Latitude of position 0
    lon1 : float
        Longitude of position 1
    lat1 : float
        Latitude of position 1

    Returns
    -------
    lon, lat
        Positions of midpoint between position 0 and position 1

    """
    bear = bearing(lon0, lat0, lon1, lat1)
    dist = haversine(lon0, lat0, lon1, lat1)

    return destination(lon0, lat0, bear, dist / 2)
