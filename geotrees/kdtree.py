"""
An implementation of KDTree using Haversine Distance for GeoSpatial analysis.
Useful tool for quickly searching for nearest neighbours. The implementation is
a K=2 or 2DTree as only 2 dimensions (longitude and latitude) are used.

Haversine distances are used for comparisons, so that the spherical geometry
of the earth is accounted for.
"""

from typing import List, Optional, Tuple

from numpy import inf

from geotrees.record import Record


class KDTree:
    """
    A Haverine distance implementation of a balanced KDTree.

    This implementation is a _balanced_ KDTree, each leaf node should have the
    same number of points (or differ by 1 depending on the number of points
    the KDTree is initialised with).

    The KDTree partitions in each of the lon and lat dimensions alternatively
    in sequence by splitting at the median of the dimension of the points
    assigned to the branch.

    Parameters
    ----------
    points : list[Record]
        A list of geotrees.Record instances.
    depth : int
        The current depth of the KDTree, you should set this to 0, it is used
        internally.
    max_depth : int
        The maximum depth of the KDTree. The leaf nodes will have depth no
        larger than this value. Leaf nodes will not be created if there is
        only 1 point in the branch.
    """

    def __init__(
        self, points: List[Record], depth: int = 0, max_depth: int = 20
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

        self.split = True

        # Left is points left of midpoint
        self.branch_left = KDTree(points[:split_index], depth + 1)
        # Right is points right of midpoint
        self.branch_right = KDTree(points[split_index:], depth + 1)

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
            return self.branch_left.insert(point)
        elif getattr(point, self.variable) > self.partition_value:
            return self.branch_right.insert(point)
        else:
            r, _ = self.query(point)
            if point in r:
                return False
            self.branch_left._insert(point)
            return True

    def _insert(self, point: Record) -> None:
        """Insert a point even if it already exists in the KDTree"""
        if not self.split:
            self.points.append(point)
            return
        if getattr(point, self.variable) <= self.partition_value:
            self.branch_left._insert(point)
        else:
            self.branch_right._insert(point)
        return

    def delete(self, point: Record) -> bool:
        """Delete a Record from the KDTree. May unbalance the KDTree"""
        if not self.split:
            try:
                self.points.remove(point)
                return True
            except ValueError:
                return False

        if getattr(point, self.variable) <= self.partition_value:
            if self.branch_left.delete(point):
                return True
        if getattr(point, self.variable) >= self.partition_value:
            if self.branch_right.delete(point):
                return True
        return False

    def query(self, point) -> Tuple[List[Record], float]:
        """Find the nearest Record within the KDTree to a query Record"""
        # Perform two checks (-180, 180) and (0, 360) longitude
        if point.lon < 0:
            point2 = Record(point.lon + 360, point.lat, fix_lon=False)
        else:
            point2 = Record(point.lon - 360, point.lat, fix_lon=False)

        r1, d1 = self._query(point)
        r2, d2 = self._query(point2)
        if d1 <= d2:
            return r1, d1
        else:
            return r2, d2

    def _query(
        self,
        point: Record,
        current_best: Optional[List[Record]] = None,
        best_distance: float = inf,
    ) -> Tuple[List[Record], float]:
        if current_best is None:
            current_best = list()
        if not self.split:
            for p in self.points:
                dist = point.distance(p)
                if dist < best_distance:
                    current_best = [p]
                    best_distance = dist
                elif dist == best_distance:
                    current_best.append(p)
            return current_best, best_distance

        if getattr(point, self.variable) <= self.partition_value:
            current_best, best_distance = self.branch_left._query(
                point, current_best, best_distance
            )
            if (
                point.distance(self._get_partition_record(point))
                <= best_distance
            ):
                current_best, best_distance = self.branch_right._query(
                    point, current_best, best_distance
                )
        else:
            current_best, best_distance = self.branch_right._query(
                point, current_best, best_distance
            )
            if (
                point.distance(self._get_partition_record(point))
                <= best_distance
            ):
                current_best, best_distance = self.branch_left._query(
                    point, current_best, best_distance
                )

        return current_best, best_distance

    def _get_partition_record(self, point: Record) -> Record:
        if self.variable == "lon":
            return Record(self.partition_value, point.lat)
        return Record(point.lon, self.partition_value)
