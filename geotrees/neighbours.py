r"""
Functions for finding nearest neighbours using bisection. Nearest neighbours can
be found with :math:`O(\log(n))` time-complexity.

Data for these functions must be sorted, otherwise incorrect values may be
returned.
"""

from bisect import bisect
from datetime import date, datetime
from typing import List, TypeVar, Union
from warnings import warn

from numpy import argmin


Numeric = TypeVar("Numeric", int, float, datetime, date)


class SortedWarning(Warning):
    """Warning class for Sortedness"""

    pass


class SortedError(Exception):
    """Error class for Sortedness"""

    pass


def _find_nearest(vals: List[Numeric], test: Numeric) -> int:
    i = bisect(vals, test)  # Position that test would be inserted

    # Handle edges
    if i == 0 and test <= vals[0]:
        return 0
    elif i == len(vals) and test >= vals[-1]:
        return len(vals) - 1

    test_idx = [i - 1, i]
    return test_idx[argmin([abs(test - vals[j]) for j in test_idx])]


def find_nearest(
    vals: List[Numeric],
    test: Union[Numeric, List[Numeric]],
    check_sorted: bool = True,
) -> Union[int, List[int]]:
    """
    Find the nearest value in a list of values for each test value.

    Uses bisection for speediness!

    Returns a list containing the index of the nearest neighbour in vals for
    each value in test. Or the index of the nearest neighbour if test is a
    single value.

    Parameters
    ----------
    vals : list[Numeric]
        List of values - this is the pool of values for which we are looking
        for a nearest match. This list MUST be sorted. Sortedness is not
        checked, nor is the list sorted.
    test : Numeric | list[Numeric]
        Query value(s)
    check_sorted : bool
        Optionally check that the input vals is sorted. Raises an error if set
        to True (default), displays a warning if set to False.

    Returns
    -------
    int | list[int]
        Index, or list of indices, of nearest value, or values.
    """
    if check_sorted:
        s = _check_sorted(vals)
        if not s:
            raise SortedError("Input values are not sorted")
    else:
        warn("Not checking sortedness of data", SortedWarning)

    if not isinstance(test, list):
        return _find_nearest(vals, test)

    return [_find_nearest(vals, t) for t in test]


def _check_sorted(vals: list[Numeric]) -> bool:
    return all(vals[i + 1] >= vals[i] for i in range(len(vals) - 1)) or all(
        vals[i + 1] <= vals[i] for i in range(len(vals) - 1)
    )
