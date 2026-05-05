import random
from string import ascii_uppercase, digits

import numpy as np
import polars as pl
import pytest

from geotrees import haversine
from geotrees.quadtree import PolarsQuadTree, QuadTree
from geotrees.record import Record
from geotrees.shape import Ellipse, Rectangle
from geotrees.utils import FailedInsertWarning


_CHARS = ascii_uppercase + digits


def _random_uid() -> str:
    return "".join([random.choice(_CHARS) for _ in range(6)])


def test_contains():
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

    test_frame = pl.from_dicts([r.__dict__ for r in points])
    res_pl = rect.check_frame(test_frame)
    assert res_pl.to_list() == expected


def test_intersection():
    rect = Rectangle(0, 20, 0, 10)
    test_rects: list[Rectangle] = [
        Rectangle(1, 19, 1, 9),
        Rectangle(20.5, 29.5, -1, 11),
        Rectangle(9, 21, 4.5, 11.5),
    ]
    expected = [True, False, True]
    res = list(map(rect.intersects, test_rects))
    assert res == expected


def test_wrap():
    rect = Rectangle(80, -100, 35, 55)
    assert rect.lon == 170
    assert rect.lat == 45
    assert rect.wraps
    test_points: list[Record] = [
        Record(-140.0, 40.0),
        Record(0.0, 50.0),
        Record(100.0, 45.0),
    ]
    expected = [True, False, True]
    res = list(map(rect.contains, test_points))
    assert res == expected

    test_frame = pl.from_dicts([r.__dict__ for r in test_points])
    res_pl = rect.check_frame(test_frame)
    assert res_pl.to_list() == expected

    test_rect = Rectangle(-140, -60, 20, 60)
    assert rect.intersects(test_rect)


def test_inside():
    # TEST: rectangle fully inside another
    outer = Rectangle(-10, 10, -10, 10)
    inner = Rectangle(-5, 5, -5, 5)

    assert outer.intersects(inner)
    assert inner.intersects(outer)


def test_divides():
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


def test_divides_pl():
    boundary = Rectangle(0, 20, 0, 8)
    qtree = PolarsQuadTree(boundary)
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


def test_insert():
    boundary = Rectangle(0, 20, 0, 8)
    qtree = QuadTree(boundary, capacity=3)
    points: list[Record] = [
        Record(10, 5),
        Record(19, 1),
        Record(0, 0),
        Record(-2, -9.2),  # Not included
        Record(12.8, 2.1),
    ]
    expected = [
        # points[:3],
        [points[0]],
        [],
        [points[2]],
        [points[1], points[-1]],
    ]
    for point in points:
        qtree.insert(point)
    assert qtree.divided
    assert qtree.len() == len(points) - 1
    res = [
        # qtree.points,
        qtree.northwest.points,
        qtree.northeast.points,
        qtree.southwest.points,
        qtree.southeast.points,
    ]
    assert res == expected


def test_insert_pl():
    boundary = Rectangle(0, 20, 0, 8)
    qtree = PolarsQuadTree(boundary, capacity=3)
    uids = ["a", "b", "c", "d", "e"]
    frame = pl.DataFrame(
        {
            "uid": uids,
            "lat": [5.0, 1.0, 0.0, -9.2, 2.1],
            "lon": [10.0, 19.0, 0.0, -2.0, 12.8],
        }
    )
    expected = [
        # uids[:3],
        [uids[0]],
        [],
        [uids[2]],
        [uids[1], uids[-1]],
    ]
    with pytest.warns(FailedInsertWarning):
        qtree.insert(frame)
    assert qtree.divided
    assert qtree.len() == frame.height - 1
    res = [
        # qtree.points,
        qtree.northwest.uids,
        qtree.northeast.uids,
        qtree.southwest.uids,
        qtree.southeast.uids,
    ]
    assert res == expected

    # TEST: Wrapping - shift to cross -180, 180
    boundary2 = Rectangle(170, -170, 0, 8)
    assert boundary2.wraps
    frame2 = frame.with_columns(pl.col("lon") + 170)
    frame2 = frame2.with_columns(
        (((pl.col("lon") + 540) % 360) - 180).alias("lon"),
    )
    qtree2 = PolarsQuadTree(boundary2, capacity=3)
    qtree2.insert(frame2)
    assert qtree2.divided
    assert qtree2.len() == frame.height - 1
    res2 = [
        # qtree2.points,
        qtree2.northwest.uids,
        qtree2.northeast.uids,
        qtree2.southwest.uids,
        qtree2.southeast.uids,
    ]
    assert res2 == expected


def test_remove():
    boundary = Rectangle(0, 20, 0, 8)
    qtree = QuadTree(boundary, capacity=3)
    points: list[Record] = [
        Record(10, 5),
        Record(19, 1),
        Record(0, 0),
        # Record(-2, -9.2),
        Record(12.8, 2.1),
    ]
    to_remove = points[2]
    for point in points:
        qtree.insert(point)
    q_res = qtree.nearby_points(to_remove, dist=0.1)

    # TEST: get the point
    assert len(q_res) == 1

    # TEST: Point is removed
    assert qtree.remove(to_remove)
    q_res = qtree.nearby_points(to_remove, dist=0.1)
    assert len(q_res) == 0


def test_remove_pl():
    boundary = Rectangle(0, 20, 0, 8)
    qtree = PolarsQuadTree(boundary, capacity=3)
    uids = ["a", "b", "c", "d", "e"]
    frame = pl.DataFrame(
        {
            "uid": uids,
            "lat": [5.0, 1.0, 0.0, -9.2, 2.1],
            "lon": [10.0, 19.0, 0.0, -2.0, 12.8],
        }
    )
    qtree.insert(frame)
    to_remove = frame.row(2, named=True)
    lat = to_remove["lat"]
    lon = to_remove["lon"]

    q_res = qtree.nearby_points(lat=lat, lon=lon, dist=0.1)

    # TEST: get the point
    assert q_res.height == 1

    res = qtree.remove(**to_remove)
    assert res

    q_res2 = qtree.nearby_points(lat=lat, lon=lon, dist=0.1)
    assert q_res2.height == 0


def test_query():
    boundary = Rectangle(0, 20, 0, 8)
    qtree = QuadTree(boundary, capacity=3)
    points: list[Record] = [
        Record(10, 5, uid="1"),
        Record(19, 1, uid="2"),
        Record(0, 0, uid="3"),
        # Record(-2, -9.2, uid="4"),
        Record(12.8, 2.1, uid="5"),
    ]
    test_rect = Rectangle(12, 13, 2, 3)
    test_point = Record(12.5, 2.2, uid="6")
    expected = [Record(12.8, 2.1, uid="5")]

    for point in points:
        qtree.insert(point)

    res = qtree.nearby_points(test_point, 200)

    assert res == expected

    res2 = qtree.query(test_rect)

    assert res2 == expected


def test_query_pl():
    boundary = Rectangle(0, 20, 0, 8)
    qtree = PolarsQuadTree(boundary, capacity=3)
    uids = ["a", "b", "c", "d", "e"]
    frame = pl.DataFrame(
        {
            "uid": uids,
            "lat": [5.0, 1.0, 0.0, -9.2, 2.1],
            "lon": [10.0, 19.0, 0.0, -2.0, 12.8],
        }
    )
    expected_uid = pl.Series(["e"])
    lat, lon = 2.2, 12.5
    qtree.insert(frame)

    res = qtree.nearby_points(lat=lat, lon=lon, dist=200)
    print(f"{res = }")
    assert res.height == 1
    assert res.get_column("uid").eq(expected_uid).all()

    test_rect = Rectangle(12, 13, 2, 3)
    res2 = qtree.query(test_rect)
    assert res.get_column("uid").equals(res2.get_column("uid"))


def test_exclude_selfquery():
    boundary = Rectangle(0, 20, 0, 8)
    qtree = QuadTree(boundary, capacity=3)
    points: list[Record] = [
        Record(10, 5, uid="1"),
        Record(19, 1, uid="2"),
        Record(0, 0, uid="3"),
        Record(-2, -9.2, uid="4"),
        Record(12.8, 2.1, uid="5"),
    ]
    test_point = Record(12.5, 2.2, uid="6")
    expected = [Record(12.8, 2.1, uid="5")]

    for point in points:
        qtree.insert(point)
    qtree.insert(test_point)

    # TEST: is not included
    res = qtree.nearby_points(test_point, 200, exclude_self=True)
    assert test_point not in res
    assert res == expected

    # TEST: is included
    res = qtree.nearby_points(test_point, 200, exclude_self=False)
    assert test_point in res

    # TEST: min_distance
    res = qtree.nearby_points(
        test_point,
        200,
        exclude_self=False,
        min_dist=50,
    )
    assert expected not in res


def test_wrap_query():
    n = 100
    qt_boundary = Rectangle(-180, 180, -90, 90)
    assert qt_boundary.lon == 0
    assert qt_boundary.lon_range == 360
    assert qt_boundary.lat == 0
    assert qt_boundary.lat_range == 180

    quadtree = QuadTree(qt_boundary, capacity=3)

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
        for _ in range(n)
    ]
    points.extend(points_want)
    for p in points:
        quadtree.insert(p)

    res = quadtree.query(quert_rect)
    assert len(res) == len(points_want)
    assert all([p in res for p in points_want])


def test_ellipse_query():
    d1 = haversine(0, 2.5, 1, 2.5)
    d2 = haversine(0, 2.5, 0, 3.0)
    theta = 0

    ellipse = Ellipse(12.5, 2.5, d1, d2, theta)
    # TEST: distinct locii
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
    n_pts = 50
    points: list[Record] = [
        Record(
            lon=20 * np.random.rand(),
            lat=8 * np.random.rand(),
            uid=_random_uid(),
        )
        for _ in range(n_pts - 2)
    ]
    # Locii
    locii = [
        Record(ellipse.p1_lon, ellipse.p1_lat, uid="locii_1"),
        Record(ellipse.p2_lon, ellipse.p2_lat, uid="locii_2"),
    ]
    outside = [
        Record(13.5, 2.6, uid="outside_1"),  # Just North of Eastern edge
        Record(12.6, 3.0, uid="outside_2"),  # Just East of Northern edge
    ]
    points.extend(locii)
    points.extend(outside)
    expected = [p for p in points if ellipse.contains(p)]

    for point in points:
        qtree.insert(point)

    res = qtree.query_ellipse(ellipse)
    print(f"{expected = }")
    print(f"{res = }")
    assert locii[0] in res
    assert locii[1] in res
    assert outside[0] not in res
    assert outside[1] not in res

    assert all(e in res for e in expected)
