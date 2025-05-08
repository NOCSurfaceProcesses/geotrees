"""
GreatCircle
-----------
Constructors and methods for interacting with GreatCircle objects, including
comparisons between GreatCircle objects.
"""

from typing import Optional, Tuple

import numpy as np

from geotrees.distance_metrics import bearing, gcd_slc


def cartesian_to_lonlat(
    x: float,
    y: float,
    z: float,
    to_radians: bool = False,
) -> Tuple[float, float]:
    """
    Get lon, and lat from cartesian coordinates.

    Parameters
    ----------
    x : float
        x coordinate
    y : float
        y coordinate
    z : float
        z coordinate
    to_radians : bool
        Return angles in radians. Otherwise return values in degrees.

    Returns
    -------
    (float, float)
    lon, lat
    """
    radius = np.sqrt(x**2 + y**2 + z**2)
    x /= radius
    y /= radius
    z /= radius
    lat = np.arcsin(z)
    tmp = np.cos(lat)
    sign = np.arcsin(y / tmp)
    lon = np.arccos(x / tmp) * sign
    if to_radians:
        return lon, lat
    return np.degrees(lon), np.degrees(lat)


def polar_to_cartesian(
    lon: float,
    lat: float,
    radius: float = 6371,
    to_radians: bool = True,
    normalised: bool = True,
) -> Tuple[float, float, float]:
    """
    Convert from polars coordinates to cartesian.

    Get cartesian coordinates from spherical polar coordinates. Default
    behaviour assumes lon and lat, so converts to radians. Set
    `to_radians=False` if the coordinates are already in radians.

    Parameters
    ----------
    lon : float
        Longitude.
    lat : float
        Latitude.
    R : float
        Radius of sphere.
    to_radians : bool
        Convert lon and lat to radians.
    normalised : bool
        Return normalised vector (ignore R value).

    Returns
    -------
    (float, float, float)
        x, y, z cartesian coordinates.
    """
    theta = np.radians(lon) if to_radians else lon
    phi = np.radians(lat) if to_radians else lat
    x = np.cos(theta) * np.cos(phi)
    y = np.sin(theta) * np.cos(phi)
    z = np.sin(phi)
    return (x, y, z) if normalised else (radius * x, radius * y, radius * z)


class GreatCircle:
    """
    A GreatCircle object for a pair of positions.

    Construct a great circle path between a pair of positions.

    https://www.boeing-727.com/Data/fly%20odds/distance.html

    Parameters
    ----------
    lon0 : float
        Longitude of start position.
    lat0 : float
        Latitude of start position.
    lon1 : float
        Longitude of end position.
    lat1 : float
        Latitude of end position.
    R : float
        Radius of the sphere. Default is Earth radius in km (6371.0).
    """

    def __init__(
        self,
        lon0: float,
        lat0: float,
        lon1: float,
        lat1: float,
        radius: float = 6371,
    ) -> None:
        self.lon0 = lon0
        self.lat0 = lat0
        self.lon1 = lon1
        self.lat1 = lat1
        self.radius = radius
        self.cross_prod = _cross_lonlat(
            self.lon0, self.lat0, self.lon1, self.lat1
        )
        self.cross_prod_dist = np.linalg.norm(self.cross_prod)
        self.bearing = bearing(self.lon0, self.lat0, self.lon1, self.lat1)
        self.dist = gcd_slc(self.lon0, self.lat0, self.lon1, self.lat1)

    def dist_from_point(
        self,
        lon: float,
        lat: float,
    ) -> float:
        """
        Compute distance from the GreatCircle to a point on the sphere.

        Parameters
        ----------
        lon : float
            Longitude of the position to test.
        lat : float
            Longitude of the position to test.

        Returns
        -------
        float
            Minimum distance between point and the GreatCircle arc.
        """
        cart = polar_to_cartesian(lon, lat, normalised=True)
        num = np.dot(cart, self.cross_prod)
        # WARN: This can be negative - hence using abs
        return np.abs(np.arcsin(num / self.cross_prod_dist) * self.radius)

    def _identical_plane(
        self,
        other: object,
        epsilon: float = 0.01,
    ) -> bool:
        """
        Identify if other GreatCircle has the same plane.

        Determined by comparing the norms of the planes constructed from the
        two points and the centre of the sphere.

        Returns True if the planes formed by the two great circles are
        parallel, i.e. the normals defining the planes have the same
        direction, or the exact opposite direction. This would mean that a
        GreatCircle compared with the GreatCircle with oppposite start and
        end points would return True.

        Parameters
        ----------
        other : GreatCircle
            Intersecting GreatCircle object
        epsilon : float
            Threshold for intersection

        Returns
        -------
        bool
            Indicating if the planes formed by two GreatCircle objects are the
            same (or mirrored) to within a given threshold.
        """
        if not isinstance(other, GreatCircle):
            raise TypeError("Input 'other' is not a GreatCircle")
        return bool(
            np.isclose(self.cross_prod, other.cross_prod, atol=epsilon).all()
            or np.isclose(
                self.cross_prod, -other.cross_prod, atol=epsilon
            ).all()
        )

    def intersection(
        self, other: object, epsilon: float = 0.01
    ) -> Optional[Tuple[float, float]]:
        """
        Determine intersection position with another GreatCircle.

        Determine the location at which the GreatCircle intersects another
        GreatCircle arc. (To within some epsilon threshold).

        Returns `None` if there is no solution - either because there is no
        intersection point, or the planes generated from the arc and centre of
        the sphere are identical.

        Parameters
        ----------
        other : GreatCircle
            Intersecting GreatCircle object
        epsilon : float
            Threshold for intersection

        Returns
        -------
        (float, float) | None
            Position of intersection
        """
        if not isinstance(other, GreatCircle):
            raise TypeError("Input 'other' is not a GreatCircle")
        if self.radius != other.radius:
            raise ValueError("GreatCircle radius values do not match")
        if self._identical_plane(other, epsilon=epsilon):
            return None
        plane_intersection = np.cross(self.cross_prod, other.cross_prod)
        epsilon *= self.radius
        s1 = plane_intersection / np.linalg.norm(plane_intersection)
        lon, lat = cartesian_to_lonlat(*s1)
        if self.dist_from_point(lon, lat) < epsilon:
            return lon, lat
        s2 = -s1
        lon, lat = cartesian_to_lonlat(*s2)
        if self.dist_from_point(lon, lat) < epsilon:
            return lon, lat
        return None

    def intersection_angle(
        self,
        other: object,
        epsilon: float = 0.01,
    ) -> Optional[float]:
        """
        Get angle of intersection with another GreatCircle.

        Get the angle of intersection with another GreatCircle arc. Returns
        None if there is no intersection.

        The intersection angle is computed using the normals of the planes
        formed by the two intersecting great circle objects.

        Parameters
        ----------
        other : GreatCircle
            Intersecting GreatCircle object
        epsilon : float
            Threshold for intersection

        Returns
        -------
        float | None
            Intersection angle in degrees
        """
        if not isinstance(other, GreatCircle):
            raise TypeError("'other' must be of type 'GreatCircle'")
        # Make sure we have an intersection!
        if self.intersection(other, epsilon) is None:
            return None
        # INFO: Want to use self.cross and other.cross which are the normals
        angle = np.arccos(
            np.dot(self.cross_prod, other.cross_prod)
            / (self.cross_prod_dist * other.cross_prod_dist)
        )
        return np.rad2deg(angle)


def _cross_lonlat(
    lon0: float,
    lat0: float,
    lon1: float,
    lat1: float,
) -> np.ndarray:
    """
    Get the cross-product between two positions on a sphere.

    |u_1| x |u_2|

    Parameters
    ----------
    lon0 : float
        Longitude of position 0 in degrees.
    lat0 : float
        Latitude of position 0 in degrees.
    lon1 : float
        Longitude of position 1 in degrees.
    lat1 : float
        Latitude of position 1 in degrees.

    Returns
    -------
    np.ndarray
        Cartesian vector of the cross product of the input lon/lat positions
        (assuming a sphere of radius 1).
    """
    return np.cross(
        polar_to_cartesian(lon0, lat0, normalised=True),
        polar_to_cartesian(lon1, lat1, normalised=True),
    )
