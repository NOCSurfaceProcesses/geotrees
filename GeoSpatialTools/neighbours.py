from numpy import argmin
from bisect import bisect
from typing import TypeVar
from datetime import date, datetime


Numeric = TypeVar("Numeric", int, float, datetime, date)


def _find_nearest(vals: list[Numeric], test: Numeric) -> int:
    i = bisect(vals, test)  # Position that test would be inserted

    # Handle edges
    if i == 0 and test <= vals[0]:
        return 0
    elif i == len(vals) and test >= vals[-1]:
        return len(vals) - 1

    test_idx = [i - 1, i]
    return test_idx[argmin([abs(test - vals[j]) for j in test_idx])]


def find_nearest(vals: list[Numeric], test: list[Numeric]) -> list[int]:
    """
    Find the nearest value in a list of values for each test value.

    Uses bisection for speediness!

    Arguments
    =========
    vals : list[Numeric]
        List of values - this is the pool of values for which we are looking
        for a nearest match. This list MUST be sorted. Sortedness is not
        checked, nor is the list sorted. An error will be raised if the list
        is not sorted.
    test : list[Numeric]
        List of query values

    Returns
    =======
    A list containing the index of the nearest neighbour in vals for each value
    in test.
    """
    return [_find_nearest(vals, t) for t in test]
