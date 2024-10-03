import unittest
from numpy import min, argmin
from GeoSpatialTools import haversine, KDTree, Record


class TestKDTree(unittest.TestCase):
    records = [
        Record(1, 2, uid="A"),
        Record(-9, 44, uid="B"),
        Record(174, -81, uid="C"),
        Record(-4, 71, uid="D"),
    ]

    def test_insert(self):
        kt = KDTree(self.records)
        test_record = Record(175, 44)
        assert kt.insert(test_record)
        assert test_record in kt.child_right.child_right.points

    def test_delete(self):
        kt = KDTree(self.records)
        delete_rec = self.records[2]
        assert delete_rec in kt.child_right.child_right.points
        assert kt.delete(delete_rec)
        assert delete_rec not in kt.child_right.child_right.points

    def test_query(self):
        kt = KDTree(self.records)
        test_record = Record(-6, 35)
        best_record, best_dist = kt.query(test_record)
        true_dist = min([test_record.distance(r) for r in self.records])
        true_ind = argmin([test_record.distance(r) for r in self.records])
        true_record = self.records[true_ind]

        self.assertAlmostEqual(true_dist, best_dist)
        assert best_record == true_record


if __name__ == "__main__":
    unittest.main()
