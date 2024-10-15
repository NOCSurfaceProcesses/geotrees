import random
import unittest
from datetime import datetime, timedelta

from GeoSpatialTools import haversine
from GeoSpatialTools.octtree import (
    OctTree,
    SpaceTimeRecord as Record,
    SpaceTimeRectangle as Rectangle,
    SpaceTimeEllipse as Ellipse,
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

    def test_intersection(self):
        d = datetime(2009, 1, 1, 0, 0)
        dt = timedelta(days=14)
        rect = Rectangle(10, 5, d, 20, 10, dt)
        test_rects: list[Rectangle] = [
            Rectangle(10, 5, d + timedelta(days=2), 18, 8, dt),
            Rectangle(25, 5, d, 9, 12, timedelta(hours=7)),
            Rectangle(
                15, 8, d - timedelta(hours=18), 12, 7, timedelta(hours=4)
            ),
            Rectangle(15, 8, d + timedelta(days=25), 12, 7, dt),
        ]
        expected = [True, False, True, False]
        res = list(map(rect.intersects, test_rects))
        assert res == expected

    def test_wrap(self):
        d = datetime(2009, 1, 1, 0, 0)
        dt = timedelta(days=14)
        rect = Rectangle(170, 45, d, 180, 20, dt)
        assert rect.east < 0
        assert rect.west > 0
        test_points: list[Record] = [
            Record(-140, 40, d),
            Record(0, 50, d),
            Record(100, 45, d - timedelta(hours=2)),
            Record(100, 45, d + timedelta(days=12)),
        ]
        expected = [True, False, True, False]
        res = list(map(rect.contains, test_points))
        assert res == expected

        test_rect = Rectangle(
            -100, 40, d + timedelta(days=3), 80, 40, timedelta(days=2)
        )
        assert test_rect.east < rect.west
        assert rect.intersects(test_rect)

        # TEST: spatially match, time fail
        test_rect = Rectangle(
            -100, 40, d + timedelta(days=13), 80, 40, timedelta(days=2)
        )
        assert not rect.intersects(test_rect)

    def test_inside(self):
        # TEST: rectangle fully inside another
        d = datetime(1978, 5, 17, 2, 33)
        dt = timedelta(days=4, hours=7)
        outer = Rectangle(-10, 10, d, -10, 10, dt)
        inner = Rectangle(-5, 5, d, -5, 5, timedelta(days=1, hours=3))

        assert outer.intersects(inner)
        assert inner.intersects(outer)


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

    def test_wrap_query(self):
        N = 100
        d = datetime(2023, 3, 24, 12, 0)
        dt = timedelta(days=10)
        boundary = Rectangle(0, 0, d, 360, 180, dt)
        ot = OctTree(boundary, capacity=3)

        quert_rect = Rectangle(
            170, 45, d + timedelta(days=4), 60, 10, timedelta(days=8)
        )
        points_want: list[Record] = [
            Record(175, 43, d + timedelta(days=2)),
            Record(-172, 49, d + timedelta(days=4)),
        ]
        points: list[Record] = [
            Record(
                random.choice(range(-150, 130)),
                random.choice(range(-90, 91)),
                d + timedelta(hours=random.choice(range(-120, 120))),
            )
            for _ in range(N)
        ]
        points.extend(points_want)
        for p in points:
            ot.insert(p)

        res = ot.query(quert_rect)
        assert len(res) == len(points_want)
        assert all([p in res for p in points_want])

    def test_ellipse_query(self):
        d1 = haversine(0, 2.5, 1, 2.5)
        d2 = haversine(0, 2.5, 0, 3.0)
        theta = 0

        d = datetime(2023, 3, 24, 12, 0)
        dt = timedelta(days=10)

        test_datetime = d + timedelta(hours=4)
        test_timedelta = timedelta(hours=5)
        ellipse = Ellipse(
            12.5, 2.5, test_datetime, d1, d2, theta, test_timedelta
        )
        # TEST: distint locii
        assert (ellipse.p1_lon, ellipse.p1_lat) != (
            ellipse.p2_lon,
            ellipse.p2_lat,
        )

        # TEST: Near Boundary Points
        assert ellipse.contains(Record(13.49, 2.5, test_datetime))
        assert ellipse.contains(Record(11.51, 2.5, test_datetime))
        assert ellipse.contains(Record(12.5, 2.99, test_datetime))
        assert ellipse.contains(Record(12.5, 2.01, test_datetime))
        assert not ellipse.contains(Record(13.51, 2.5, test_datetime))
        assert not ellipse.contains(Record(11.49, 2.5, test_datetime))
        assert not ellipse.contains(Record(12.5, 3.01, test_datetime))
        assert not ellipse.contains(Record(12.5, 1.99, test_datetime))

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
            Record(12.6, 2.1, d + timedelta(hours=2), "northeastfwd"),
            Record(13.5, 2.6, test_datetime, "too north of eastern edge"),
            Record(12.6, 3.0, test_datetime, "too east of northern edge"),
            # Locii
            Record(ellipse.p1_lon, ellipse.p1_lat, test_datetime, "locii1"),
            Record(ellipse.p2_lon, ellipse.p2_lat, test_datetime, "locii2"),
        ]
        expected = [
            Record(12.6, 2.1, d + timedelta(hours=2), "northeastfwd"),
            Record(ellipse.p1_lon, ellipse.p1_lat, test_datetime, "locii1"),
            Record(ellipse.p2_lon, ellipse.p2_lat, test_datetime, "locii2"),
        ]

        for point in points:
            otree.insert(point)

        res = otree.query_ellipse(ellipse)
        assert res == expected


if __name__ == "__main__":
    unittest.main()
