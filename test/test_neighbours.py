import unittest
from datetime import datetime, timedelta
from random import choice, sample

from numpy import argmin

from geotrees import find_nearest
from geotrees.neighbours import SortedError, SortedWarning


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

    def test_sorted_warn(self):
        with self.assertWarns(SortedWarning):
            find_nearest([1.0, 2.0, 3.0], 2.3, check_sorted=False)

    def test_sorted_error(self):
        with self.assertRaises(SortedError):
            find_nearest([3.0, 1.0, 2.0], 2.3)


if __name__ == "__main__":
    unittest.main()
