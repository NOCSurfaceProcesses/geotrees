import random
import unittest

from GeoSpatialTools import haversine
from GeoSpatialTools.quadtree import QuadTree, Record, Rectangle, Ellipse


class TestRect(unittest.TestCase):
    def test_contains(self):
        rect = Rectangle(0, 20, 0, 10)
        points: list[Record] = [
            Record(10, 5),
            Record(20, 10),
            Record(0, 0),
            Record(12.8, 2.1),
            Record(-2, -9.2),
        ]
        expected = [True, True, True, True, False]
        res = list(map(rect.contains, points))
        assert res == expected

    def test_intersection(self):
        rect = Rectangle(0, 20, 0, 10)
        test_rects: list[Rectangle] = [
            Rectangle(1, 19, 1, 9),
            Rectangle(20.5, 29.5, -1, 11),
            Rectangle(9, 21, 4.5, 11.5),
        ]
        expected = [True, False, True]
        res = list(map(rect.intersects, test_rects))
        assert res == expected

    def test_wrap(self):
        rect = Rectangle(80, -100, 35, 55)
        assert rect.lon == 170
        assert rect.lat == 45
        test_points: list[Record] = [
            Record(-140, 40),
            Record(0, 50),
            Record(100, 45),
        ]
        expected = [True, False, True]
        res = list(map(rect.contains, test_points))
        assert res == expected

        test_rect = Rectangle(-140, -60, 20, 60)
        assert rect.intersects(test_rect)


class TestQuadTree(unittest.TestCase):
    def test_divides(self):
        boundary = Rectangle(0, 20, 0, 8)
        qtree = QuadTree(boundary)
        expected: list[Rectangle] = [
            Rectangle(0, 10, 4, 8),
            Rectangle(10, 20, 4, 8),
            Rectangle(0, 10, 0, 4),
            Rectangle(10, 20, 0, 4),
        ]
        qtree.divide()
        res = [
            qtree.northwest.boundary,
            qtree.northeast.boundary,
            qtree.southwest.boundary,
            qtree.southeast.boundary,
        ]
        assert res == expected

    def test_insert(self):
        boundary = Rectangle(0, 20, 0, 8)
        qtree = QuadTree(boundary, capacity=3)
        points: list[Record] = [
            Record(10, 5),
            Record(19, 1),
            Record(0, 0),
            Record(-2, -9.2),
            Record(12.8, 2.1),
        ]
        expected = [
            points[:3],
            [],
            [],
            [],
            [points[-1]],
        ]
        for point in points:
            qtree.insert(point)
        assert qtree.divided
        res = [
            qtree.points,
            qtree.northwest.points,
            qtree.northeast.points,
            qtree.southwest.points,
            qtree.southeast.points,
        ]
        assert res == expected

    def test_query(self):
        boundary = Rectangle(0, 20, 0, 8)
        qtree = QuadTree(boundary, capacity=3)
        points: list[Record] = [
            Record(10, 5),
            Record(19, 1),
            Record(0, 0),
            Record(-2, -9.2),
            Record(12.8, 2.1),
        ]
        test_rect = Rectangle(12, 13, 2, 3)
        expected = [Record(12.8, 2.1)]

        for point in points:
            qtree.insert(point)

        res = qtree.query(test_rect)

        assert res == expected

    def test_wrap_query(self):
        N = 100
        qt_boundary = Rectangle(-180, 180, -90, 90)
        assert qt_boundary.lon == 0
        assert qt_boundary.lon_range == 360
        assert qt_boundary.lat == 0
        assert qt_boundary.lat_range == 180

        qt = QuadTree(qt_boundary, capacity=3)

        quert_rect = Rectangle(140, -160, 40, 50)
        assert quert_rect.lon == 170
        assert quert_rect.lon_range == 60
        assert quert_rect.lat == 45
        assert quert_rect.lat_range == 10

        points_want: list[Record] = [
            Record(175, 43),
            Record(-172, 49),
        ]
        points: list[Record] = [
            Record(
                random.choice(range(-150, 130)),
                random.choice(range(-90, 91)),
            )
            for _ in range(N)
        ]
        points.extend(points_want)
        for p in points:
            qt.insert(p)

        res = qt.query(quert_rect)
        assert len(res) == len(points_want)
        assert all([p in res for p in points_want])

    def test_ellipse_query(self):
        d1 = haversine(0, 2.5, 1, 2.5)
        d2 = haversine(0, 2.5, 0, 3.0)
        theta = 0

        ellipse = Ellipse(12.5, 2.5, d1, d2, theta)
        # TEST: distint locii
        assert (ellipse.p1_lon, ellipse.p1_lat) != (
            ellipse.p2_lon,
            ellipse.p2_lat,
        )

        # TEST: Near Boundary Points
        assert ellipse.contains(Record(13.49, 2.5))
        assert ellipse.contains(Record(11.51, 2.5))
        assert ellipse.contains(Record(12.5, 2.99))
        assert ellipse.contains(Record(12.5, 2.01))
        assert not ellipse.contains(Record(13.51, 2.5))
        assert not ellipse.contains(Record(11.49, 2.5))
        assert not ellipse.contains(Record(12.5, 3.01))
        assert not ellipse.contains(Record(12.5, 1.99))

        boundary = Rectangle(0, 20, 0, 8)
        qtree = QuadTree(boundary, capacity=3)
        points: list[Record] = [
            Record(10, 5),
            Record(19, 1),
            Record(0, 0),
            Record(-2, -9.2),
            Record(13.5, 2.6),  # Just North of Eastern edge
            Record(12.6, 3.0),  # Just East of Northern edge
            Record(12.8, 2.1),
            # Locii
            Record(ellipse.p1_lon, ellipse.p1_lat),
            Record(ellipse.p2_lon, ellipse.p2_lat),
        ]
        expected = [
            Record(12.8, 2.1),
            Record(ellipse.p1_lon, ellipse.p1_lat),
            Record(ellipse.p2_lon, ellipse.p2_lat),
        ]

        for point in points:
            qtree.insert(point)

        res = qtree.query_ellipse(ellipse)
        assert res == expected


if __name__ == "__main__":
    unittest.main()
