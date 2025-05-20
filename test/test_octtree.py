import random
import unittest
from datetime import datetime, timedelta

from geotrees import haversine
from geotrees.octtree import OctTree
from geotrees.record import SpaceTimeRecord as Record
from geotrees.shape import (
    SpaceTimeEllipse as Ellipse,
)
from geotrees.shape import (
    SpaceTimeRectangle as Rectangle,
)
from geotrees.utils import DateWarning


class TestRect(unittest.TestCase):
    def test_contains(self):
        d = datetime(2009, 1, 1, 0, 0)
        dt = timedelta(days=7)
        start = d - dt
        end = d + dt
        rect = Rectangle(0, 20, 0, 10, start, end)
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
        dt = timedelta(days=7)
        start = d - dt
        end = d + dt
        rect = Rectangle(0, 20, 0, 10, start, end)

        test_rects: list[Rectangle] = [
            Rectangle(
                1, 19, 1, 9, d - timedelta(days=1), d + timedelta(days=1)
            ),
            Rectangle(
                20.5,
                29.5,
                -1,
                11,
                d - timedelta(hours=7),
                d + timedelta(hours=7),
            ),
            Rectangle(
                9,
                21,
                4.5,
                11.5,
                d - timedelta(hours=20),
                d - timedelta(hours=16),
            ),
            Rectangle(
                9, 21, 4.5, 11.5, d + timedelta(days=25), d + timedelta(days=27)
            ),
        ]
        expected = [True, False, True, False]
        res = list(map(rect.intersects, test_rects))
        assert res == expected

    def test_wrap(self):
        d = datetime(2009, 1, 1, 0, 0)
        dt = timedelta(days=7)
        start = d - dt
        end = d + dt
        rect = Rectangle(80, -100, 35, 55, start, end)

        assert rect.lon == 170
        assert rect.lat == 45

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
            -140,
            60,
            20,
            60,
            d + timedelta(days=2),
            d + timedelta(days=4),
        )
        assert test_rect.east < rect.west
        assert rect.intersects(test_rect)

        # TEST: spatially match, time fail
        test_rect = Rectangle(
            -140,
            60,
            20,
            60,
            d + timedelta(days=12),
            d + timedelta(days=14),
        )
        assert not rect.intersects(test_rect)

    def test_swap_date(self):
        d = datetime(2009, 1, 1, 0, 0)
        dt = timedelta(days=7)
        start = d - dt
        end = d + dt
        with self.assertWarns(DateWarning):
            rect = Rectangle(80, -100, 35, 55, end, start)

        assert rect.start == start
        assert rect.end == end

    def test_inside(self):
        # TEST: rectangle fully inside another
        d = datetime(2009, 1, 1, 0, 0)
        dt = timedelta(days=7)
        start = d - dt
        end = d + dt

        outer = Rectangle(-10, 10, -10, 10, start, end)
        inner = Rectangle(
            -5, 5, -5, 5, start + timedelta(days=1), end - timedelta(days=1)
        )

        assert outer.intersects(inner)
        assert inner.intersects(outer)


class TestOctTree(unittest.TestCase):
    def test_divides(self):
        d = datetime(2023, 3, 24, 12, 0)
        dt = timedelta(days=1)
        start = d - dt / 2
        end = d + dt / 2

        # TEST: Could construct start and ends for OctTree branches using
        #       the start and end of the boundary, but I want to verify that
        #       the values are what I expect
        d1 = datetime(2023, 3, 24, 6, 0)
        d2 = datetime(2023, 3, 24, 18, 0)
        dt2 = timedelta(hours=12)
        start1 = d1 - dt2 / 2
        end1 = d1 + dt2 / 2
        start2 = d2 - dt2 / 2
        end2 = d2 + dt2 / 2

        boundary = Rectangle(0, 20, 0, 8, start, end)
        otree = OctTree(boundary)
        expected: list[Rectangle] = [
            Rectangle(0, 10, 4, 8, start1, end1),
            Rectangle(10, 20, 4, 8, start1, end1),
            Rectangle(0, 10, 0, 4, start1, end1),
            Rectangle(10, 20, 0, 4, start1, end1),
            Rectangle(0, 10, 4, 8, start2, end2),
            Rectangle(10, 20, 4, 8, start2, end2),
            Rectangle(0, 10, 0, 4, start2, end2),
            Rectangle(10, 20, 0, 4, start2, end2),
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
        start = d - dt
        end = d + dt

        boundary = Rectangle(0, 20, 0, 8, start, end)
        otree = OctTree(boundary, capacity=3)
        points: list[Record] = [
            Record(10, 4, d, "northwestback1"),
            Record(12, 1, d + timedelta(hours=3), "southeastfwd"),
            Record(3, 7, d - timedelta(days=3), "northeastback2"),
            Record(13, 2, d + timedelta(hours=17), "southeastfwd"),
            Record(13, 6, d - timedelta(days=1), "northwestback1"),
            Record(10.01, 4, d, "northeastback2"),
            Record(18, 2, d + timedelta(days=23), "not added"),
            Record(11, 7, d + timedelta(hours=2), "northeastfwd"),
        ]
        for point in points:
            otree.insert(point)
        assert otree.len() == len(points) - 1  # NOTE: 1 point not added
        assert otree.divided
        expected = [
            # points[:3],
            [points[2], points[0]],
            [points[4], points[5]],
            [],
            [],
            [],
            [points[-1]],
            [points[3], points[1]],
            [],
        ]
        res = [
            # otree.points,
            otree.northwestback.points,
            otree.northeastback.points,
            otree.southwestback.points,
            otree.southeastback.points,
            otree.northwestfwd.points,
            otree.northeastfwd.points,
            otree.southeastfwd.points,
            otree.southwestfwd.points,
        ]
        assert points[-2] not in res
        assert len(otree.points) == 0
        for ex, r in zip(expected, res):
            assert all(e in r for e in ex)

    def test_remove(self):
        d = datetime(2023, 3, 24, 12, 0)
        dt = timedelta(days=10)
        start = d - dt
        end = d + dt

        boundary = Rectangle(0, 20, 0, 8, start, end)
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
        to_remove = points[4]
        for point in points:
            otree.insert(point)

        # TEST: query works before remove
        q_res = otree.nearby_points(
            to_remove, dist=0.1, t_dist=timedelta(minutes=5)
        )
        assert len(q_res) == 1

        # TEST: point is removed and query fails
        assert otree.remove(to_remove)
        q_res = otree.nearby_points(
            to_remove, dist=0.1, t_dist=timedelta(minutes=5)
        )
        assert len(q_res) == 0

    def test_query(self):
        d = datetime(2023, 3, 24, 12, 0)
        dt = timedelta(days=10)
        start = d - dt
        end = d + dt
        boundary = Rectangle(0, 20, 0, 8, start, end)
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
        test_rect = Rectangle(10, 11.5, 6.5, 7.5, d, d + timedelta(hours=6))
        expected = [Record(11, 7, d + timedelta(hours=2), "northeastfwd")]

        res = otree.nearby_points(
            test_point, dist=200, t_dist=timedelta(hours=5)
        )

        assert res == expected

        res2 = otree.query(test_rect)

        assert res2 == expected

    def test_exclude_query(self):
        d = datetime(2023, 3, 24, 12, 0)
        dt = timedelta(days=10)
        start = d - dt
        end = d + dt
        boundary = Rectangle(0, 20, 0, 8, start, end)
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
        test_point = Record(11, 6, d + timedelta(hours=4), "test")
        otree.insert(test_point)

        expected = [Record(11, 7, d + timedelta(hours=2), "northeastfwd")]

        # TEST: is not included
        res = otree.nearby_points(
            test_point,
            dist=200,
            t_dist=timedelta(hours=5),
            exclude_self=True,
        )

        assert test_point not in res
        assert res == expected

        # TEST: is included
        res = otree.nearby_points(
            test_point,
            dist=200,
            t_dist=timedelta(hours=5),
            exclude_self=False,
        )
        assert test_point in res

    def test_wrap_query(self):
        n = 100
        d = datetime(2023, 3, 24, 12, 0)
        dt = timedelta(days=10)
        start = d - dt
        end = d + dt
        boundary = Rectangle(-180, 180, -90, 90, start, end)
        octree = OctTree(boundary, capacity=3)

        quert_rect = Rectangle(140, -160, 40, 50, d, d + timedelta(days=8))
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
            for _ in range(n)
        ]
        points.extend(points_want)
        for p in points:
            octree.insert(p)

        res = octree.query(quert_rect)
        assert len(res) == len(points_want)
        assert all([p in res for p in points_want])

    def test_ellipse_query(self):
        d1 = haversine(0, 2.5, 1, 2.5)
        d2 = haversine(0, 2.5, 0, 3.0)
        theta = 0

        d = datetime(2023, 3, 24, 12, 0)
        dt = timedelta(days=10)
        start = d - dt
        end = d + dt

        test_datetime = d + timedelta(hours=4)
        test_timedelta = timedelta(hours=5)

        ellipse = Ellipse(
            12.5,
            2.5,
            d1,
            d2,
            theta,
            test_datetime - test_timedelta / 2,
            test_datetime + test_timedelta / 2,
        )
        # TEST: distinct locii
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

        boundary = Rectangle(0, 20, 0, 8, start, end)

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
            Record(ellipse.p1_lon, ellipse.p1_lat, test_datetime, "locii1"),
            Record(ellipse.p2_lon, ellipse.p2_lat, test_datetime, "locii2"),
            Record(12.6, 2.1, d + timedelta(hours=2), "northeastfwd"),
        ]

        for point in points:
            otree.insert(point)

        res = otree.query_ellipse(ellipse)
        assert all(e in res for e in expected)


if __name__ == "__main__":
    unittest.main()
