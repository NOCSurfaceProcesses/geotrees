import unittest

import numpy as np

from geotrees.distance_metrics import gcd_slc
from geotrees.great_circle import GreatCircle


class TestGreatCircle(unittest.TestCase):
    halifax = (-63.5728, 44.6476)
    southampton = (-1.4049, 50.9105)

    def test_constructor(self):
        out = GreatCircle(*self.halifax, *self.southampton)
        assert hasattr(out, "dist")
        assert out.dist == gcd_slc(*self.southampton, *self.halifax)

    def test_meridian_planes(self):
        # TEST: That great circles from a pole stay on the same longitude
        lon0, lat0 = 45, 23
        gc1 = GreatCircle(0, 90, lon0, lat0)

        assert gc1.dist_from_point(-lon0, lat0 + 5) > 10
        for lat in range(lat0, 90, 2):
            dist = gc1.dist_from_point(lon0, lat)
            assert dist < 0.01

        gc2 = GreatCircle(0, -90, lon0, -lat0)
        assert abs(gc1.dist - gc2.dist) < 0.01
        for lat in range(-lat0, -90, -2):
            dist = gc2.dist_from_point(lon0, lat)
            assert dist < 0.01

        assert gc1._identical_plane(gc2)

    def test_equator_vs_meridian(self):
        # TEST: that a great circle at the equator and a line of longitude
        #   intersect with angle 90
        gc0 = GreatCircle(-5, 0, 5, 0)
        gc1 = GreatCircle(0, -5, 0, 5)
        assert np.isclose([gc0.dist], [gc1.dist]).all()
        assert gc1.dist_from_point(0, 0) < 0.01
        # assert GC0.dist_from_point(0, 0) < 0.01

        int_pts = gc0.intersection(gc1)
        int_ang = gc0.intersection_angle(gc1)
        assert int_pts == (0, 0)
        assert int_ang == 90
