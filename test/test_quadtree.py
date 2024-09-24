import unittest
from GeoSpatialTools.quadtree import QuadTree, Record, Rectangle


class TestRect(unittest.TestCase):
    def test_contains(self):
        rect = Rectangle(10, 5, 20, 10)
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
        rect = Rectangle(10, 5, 20, 10)
        test_rects: list[Rectangle] = [
            Rectangle(10, 5, 18, 8),
            Rectangle(25, 5, 9, 12),
            Rectangle(15, 8, 12, 7),
        ]
        expected = [True, False, True]
        res = list(map(rect.intersects, test_rects))
        assert res == expected


class TestQuadTree(unittest.TestCase):
    def test_divides(self):
        boundary = Rectangle(10, 4, 20, 8)
        qtree = QuadTree(boundary)
        expected: list[Rectangle] = [
            Rectangle(5, 6, 10, 4),
            Rectangle(15, 6, 10, 4),
            Rectangle(5, 2, 10, 4),
            Rectangle(15, 2, 10, 4),
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
        boundary = Rectangle(10, 4, 20, 8)
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
        boundary = Rectangle(10, 4, 20, 8)
        qtree = QuadTree(boundary, capacity=3)
        points: list[Record] = [
            Record(10, 5),
            Record(19, 1),
            Record(0, 0),
            Record(-2, -9.2),
            Record(12.8, 2.1),
        ]
        test_rect = Rectangle(12.5, 2.5, 1, 1)
        expected = [Record(12.8, 2.1)]

        for point in points:
            qtree.insert(point)

        res = qtree.query(test_rect)

        assert res == expected


if __name__ == "__main__":
    unittest.main()
