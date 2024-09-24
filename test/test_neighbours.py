import unittest
from numpy import argmin
from random import choice, sample
from datetime import datetime, timedelta
from GeoSpatialTools import find_nearest


class TestFindNearest(unittest.TestCase):
    dates = [
        datetime(2009, 1, 1, 0, 0) + timedelta(seconds=i * 3600)
        for i in range(365 * 24)
    ]
    test_dates = sample(dates, 150)
    test_dates = [
        d + timedelta(seconds=60 * choice(range(60))) for d in test_dates
    ]
    test_dates.append(dates[0])
    test_dates.append(dates[-1])
    test_dates.append(datetime(2004, 11, 15, 17, 28))
    test_dates.append(datetime(2013, 4, 22, 1, 41))

    def test_nearest(self):
        greedy = [
            argmin([abs(x - y) for x in self.dates]) for y in self.test_dates
        ]
        ours = find_nearest(self.dates, self.test_dates)

        assert ours == greedy

    pass


if __name__ == "__main__":
    unittest.main()
