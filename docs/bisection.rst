================
Bisection Search
================

Bisection can be used to find the nearest neighbour in a sorted one-dimensional list of search values in
:math:`O(\log(n))` time complexity.

The implementation in `geotrees` makes use of the `bisect` library, which is part of the Python standard library.
The input types are numeric types, which can include ``int``, ``float``, or ``datetime.datetime`` values.

The bisection approach repeatedly splits the list of search values in two at the mid-index. The query value is compared
to the search value at the mid-index. If the query value is larger than the search value at the mid-index, then the
search values after the mid-index become the new search values. If the query value is smaller than the search value at
the mid-index then the search values before the mid-index become the new search values. This bisecting is repeated
(succesively halving the number of search values) until one values remain. The nearest neighbour is either the value at
the remaining index, or the value at the index one above.

.. note:: The above assumes that the list of search values is sorted in increasing order. The opposite applies if the
   list is sorted in reverse.

.. warning:: The input values must be sorted

Example
=======

.. code-block:: python

   from geotrees import find_nearest
   import numpy as np

   search_values: list[float] = list(np.random.randn(50))
   search_values.sort()

   query_value: float = 0.45
   neighbour_index: int = find_nearest(
        vals=search_values,
        test=query_value,
   )
   neighbour_value: float = search_values[neighbour_index]

neighbours Module
=================

.. automodule:: geotrees.neighbours
   :members:
