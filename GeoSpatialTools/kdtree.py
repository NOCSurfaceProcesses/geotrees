"""
An implementation of KDTree using Haversine Distance for GeoSpatial analysis.
Useful tool for quickly searching for nearest neighbours.
"""

from . import Record
from numpy import inf


class KDTree:
    """
    A Haverine distance implementation of a balanced KDTree.

    This implementation is a _balanced_ KDTree, each leaf node should have the
    same number of points (or differ by 1 depending on the number of points
    the KDTree is intialised with).

    The KDTree partitions in each of the lon and lat dimensions alternatively
    in sequence by splitting at the median of the dimension of the points
    assigned to the branch.

    Parameters
    ----------
    points : list[Record]
        A list of GeoSpatialTools.Record instances.
    depth : int
        The current depth of the KDTree, you should set this to 0, it is used
        internally.
    max_depth : int
        The maximium depth of the KDTree. The leaf nodes will have depth no
        larger than this value. Leaf nodes will not be created if there is
        only 1 point in the branch.
    """

    def __init__(
        self, points: list[Record], depth: int = 0, max_depth: int = 20
    ) -> None:
        self.depth = depth
        n_points = len(points)

        if self.depth == max_depth or n_points < 2:
            self.points = points
            self.split = False
            return None

        self.axis = depth % 2
        self.variable = "lon" if self.axis == 0 else "lat"

        points.sort(key=lambda p: getattr(p, self.variable))
        split_index = n_points // 2
        self.partition_value = getattr(points[split_index - 1], self.variable)
        while (
            split_index < n_points
            and getattr(points[split_index], self.variable)
            == self.partition_value
        ):
            split_index += 1

        self.split = True

        # Left is <= median
        self.child_left = KDTree(points[:split_index], depth + 1)
        # Right is > median
        self.child_right = KDTree(points[split_index:], depth + 1)

        return None

    def insert(self, point: Record) -> bool:
        """
        Insert a Record into the KDTree. May unbalance the KDTree.

        The point will not be inserted if it is already in the KDTree.
        """
        if not self.split:
            if point in self.points:
                return False
            self.points.append(point)
            return True

        if getattr(point, self.variable) < self.partition_value:
            return self.child_left.insert(point)
        else:
            return self.child_right.insert(point)

    def delete(self, point: Record) -> bool:
        """Delete a Record from the KDTree. May unbalance the KDTree"""
        if not self.split:
            try:
                self.points.remove(point)
                return True
            except ValueError:
                return False

        if getattr(point, self.variable) < self.partition_value:
            return self.child_left.delete(point)
        else:
            return self.child_right.delete(point)

    def query(self, point) -> tuple[Record | None, float]:
        """Find the nearest Record within the KDTree to a query Record"""
        if point.lon < 0:
            point2 = Record(point.lon + 360, point.lat)
        else:
            point2 = Record(point.lon - 360, point.lat)

        r1, d1 = self._query(point)
        r2, d2 = self._query(point2)
        if d1 <= d2:
            r = r1
        else:
            r = r2
        return r, point.distance(r)

    def _query(
        self,
        point: Record,
        current_best: Record | None = None,
        best_distance: float = inf,
    ) -> tuple[Record | None, float]:
        if not self.split:
            for p in self.points:
                dist = point.distance(p)
                if dist < best_distance:
                    current_best = p
                    best_distance = dist
            return current_best, best_distance

        if getattr(point, self.variable) < self.partition_value:
            current_best, best_distance = self.child_left._query(
                point, current_best, best_distance
            )
            if (
                point.distance(self._get_partition_record(point))
                < best_distance
            ):
                current_best, best_distance = self.child_right._query(
                    point, current_best, best_distance
                )
        else:
            current_best, best_distance = self.child_right._query(
                point, current_best, best_distance
            )
            if (
                point.distance(self._get_partition_record(point))
                < best_distance
            ):
                current_best, best_distance = self.child_left._query(
                    point, current_best, best_distance
                )

        return current_best, best_distance

    def _get_partition_record(self, point: Record) -> Record:
        if self.variable == "lon":
            return Record(self.partition_value, point.lat)
        return Record(point.lon, self.partition_value)
