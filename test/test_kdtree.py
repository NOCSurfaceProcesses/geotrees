import random
import unittest

from numpy import argmin, min

from geotrees import KDTree, Record


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
        assert test_record in kt.branch_right.branch_right.points

    def test_delete(self):
        kt = KDTree(self.records)
        delete_rec = self.records[2]
        assert delete_rec in kt.branch_right.branch_right.points
        assert kt.delete(delete_rec)
        assert delete_rec not in kt.branch_right.branch_right.points

    def test_delete_dup(self):
        test_records = [
            Record(45, -23, uid="1"),
            Record(45, -23, uid="2"),
            Record(45, -23, uid="3"),
            Record(45, -23, uid="4"),
        ]
        kt = KDTree(test_records, max_depth=3)
        assert kt.delete(test_records[1])
        # TEST: Cannot delete same record twice!
        assert not kt.delete(test_records[1])

    def test_query(self):
        kt = KDTree(self.records)
        test_record = Record(-6, 35)
        best_record, best_dist = kt.query(test_record)
        true_dist = min([test_record.distance(r) for r in self.records])
        true_ind = argmin([test_record.distance(r) for r in self.records])
        true_record = self.records[true_ind]

        self.assertAlmostEqual(true_dist, best_dist)
        assert len(best_record) == 1
        assert best_record[0] == true_record

    def test_duplicated_pos(self):
        # TEST: That equal records get partitioned equally
        test_records = [
            Record(45, -23, uid="1"),
            Record(45, -23, uid="2"),
            Record(45, -23, uid="3"),
            Record(45, -23, uid="4"),
        ]
        kt = KDTree(test_records, max_depth=3)
        assert len(kt.branch_left.branch_left.points) == 1
        assert len(kt.branch_left.branch_right.points) == 1
        assert len(kt.branch_right.branch_left.points) == 1
        assert len(kt.branch_right.branch_right.points) == 1

    def test_insert_dup(self):
        test_records = [
            Record(45, -23, uid="1"),
            Record(45, -23, uid="2"),
            Record(45, -23, uid="3"),
            Record(45, -23, uid="4"),
        ]
        kt = KDTree(test_records, max_depth=3)
        assert not kt.insert(test_records[0])
        assert not kt.insert(test_records[1])
        assert not kt.insert(test_records[2])
        assert not kt.insert(test_records[3])
        assert kt.insert(Record(45, -23, uid="5"))
        assert not kt.insert(Record(45, -23, uid="5"))
        # TEST: Can insert after deleting
        assert kt.delete(Record(45, -23, uid="5"))
        assert kt.insert(Record(45, -23, uid="5"))

    def test_get_multiple_neighbours(self):
        kt = KDTree(self.records)
        kt.insert(Record(45, -21, uid="1"))
        kt.insert(Record(45, -21, uid="2"))

        r, _ = kt.query(Record(44, -21, uid="3"))
        assert len(r) == 2

    def test_wrap(self):
        # TEST: Accounts for wrap at -180, 180
        kt = KDTree(self.records)
        bad_rec = Record(-160, -64, uid="G")
        kt.insert(bad_rec)
        query_rec = Record(-178, -79, uid="E")
        r, _ = kt.query(query_rec)
        assert len(r) == 1
        assert r[0].uid == "C"

    def test_near_pole_query(self):
        test_records = [
            Record(-180, 89.5, uid="1"),
            Record(-90, 89.9, uid="2"),
            Record(0, 89.5, uid="3"),
        ]
        n_others = 50
        test_records.extend(
            [
                Record(
                    random.choice(range(-180, 180)),
                    random.choice(range(80, 90)),
                )
                for _ in range(n_others)
            ]
        )

        kt = KDTree(test_records, max_depth=3)

        query_rec = Record(90, 89.8, uid="4")
        r, d = kt.query(query_rec)
        assert len(r) == 1
        print(r[0])
        print(d)
        assert r[0].uid == "2"


if __name__ == "__main__":
    unittest.main()
