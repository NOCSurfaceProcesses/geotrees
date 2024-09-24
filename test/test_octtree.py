import unittest
from datetime import datetime, timedelta

from GeoSpatialTools.octtree import (
    OctTree,
    SpaceTimeRecord as Record,
    SpaceTimeRectangle as Rectangle,
)


class TestRect(unittest.TestCase):
    def test_contains(self):
        d = datetime(2009, 1, 1, 0, 0)
        dt = timedelta(days=14)
        rect = Rectangle(10, 5, d, 20, 10, dt)
        points: list[Record] = [
            Record(10, 5, d),
            Record(20, 10, d + timedelta(hours=4)),
            Record(20, 10, datetime(2010, 4, 12, 13, 15)),
            Record(0, 0, d - timedelta(days=6)),
            Record(12.8, 2.1, d + timedelta(days=-1)),
            Record(-2, -9.2, d),
        ]
        expected = [True, True, False, True, True, False]
        res = list(map(rect.contains, points))
        assert res == expected


class TestOctTree(unittest.TestCase):
    def test_divides(self):
        d = datetime(2023, 3, 24, 12, 0)
        dt = timedelta(days=1)

        d1 = datetime(2023, 3, 24, 6, 0)
        d2 = datetime(2023, 3, 24, 18, 0)
        dt2 = timedelta(hours=12)

        boundary = Rectangle(10, 4, d, 20, 8, dt)
        otree = OctTree(boundary)
        expected: list[Rectangle] = [
            Rectangle(5, 6, d1, 10, 4, dt2),
            Rectangle(15, 6, d1, 10, 4, dt2),
            Rectangle(5, 2, d1, 10, 4, dt2),
            Rectangle(15, 2, d1, 10, 4, dt2),
            Rectangle(5, 6, d2, 10, 4, dt2),
            Rectangle(15, 6, d2, 10, 4, dt2),
            Rectangle(5, 2, d2, 10, 4, dt2),
            Rectangle(15, 2, d2, 10, 4, dt2),
        ]
        otree.divide()
        res = [
            otree.northwestback.boundary,
            otree.northeastback.boundary,
            otree.southwestback.boundary,
            otree.southeastback.boundary,
            otree.northwestfwd.boundary,
            otree.northeastfwd.boundary,
            otree.southwestfwd.boundary,
            otree.southeastfwd.boundary,
        ]
        assert res == expected

    def test_insert(self):
        d = datetime(2023, 3, 24, 12, 0)
        dt = timedelta(days=10)
        boundary = Rectangle(10, 4, d, 20, 8, dt)
        otree = OctTree(boundary, capacity=3)
        points: list[Record] = [
            Record(10, 4, d, "main"),
            Record(12, 1, d + timedelta(hours=3), "main2"),
            Record(3, 7, d - timedelta(days=3), "main3"),
            Record(13, 2, d + timedelta(hours=17), "southeastfwd"),
            Record(3, 6, d - timedelta(days=1), "northwestback"),
            Record(10, 4, d, "northwestback"),
            Record(18, 2, d + timedelta(days=23), "not added"),
            Record(11, 7, d + timedelta(hours=2), "northeastfwd"),
        ]
        for point in points:
            otree.insert(point)
        assert otree.divided
        expected = [
            points[:3],
            points[4:6],
            [],
            [],
            [],
            [],
            [points[-1]],
            [],
            [points[3]],
        ]
        res = [
            otree.points,
            otree.northwestback.points,
            otree.northeastback.points,
            otree.southwestback.points,
            otree.southeastback.points,
            otree.northwestfwd.points,
            otree.northeastfwd.points,
            otree.southwestfwd.points,
            otree.southeastfwd.points,
        ]
        assert res == expected

    def test_query(self):
        d = datetime(2023, 3, 24, 12, 0)
        dt = timedelta(days=10)
        boundary = Rectangle(10, 4, d, 20, 8, dt)
        otree = OctTree(boundary, capacity=3)
        points: list[Record] = [
            Record(10, 4, d, "main"),
            Record(12, 1, d + timedelta(hours=3), "main2"),
            Record(3, 7, d - timedelta(days=3), "main3"),
            Record(13, 2, d + timedelta(hours=17), "southeastfwd"),
            Record(3, 6, d - timedelta(days=1), "northwestback"),
            Record(10, 4, d, "northwestback"),
            Record(18, 2, d + timedelta(days=23), "not added"),
            Record(11, 7, d + timedelta(hours=2), "northeastfwd"),
        ]
        for point in points:
            otree.insert(point)
        test_point = Record(11, 6, d + timedelta(hours=4))
        expected = [Record(11, 7, d + timedelta(hours=2), "northeastfwd")]

        res = otree.nearby_points(
            test_point, dist=200, t_dist=timedelta(hours=5)
        )

        assert res == expected


if __name__ == "__main__":
    unittest.main()
