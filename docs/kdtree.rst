========
K-D-Tree
========

A K-D-Tree is a data structure that operates in a similar way to bisection or a binary tree, and can be used to find the
nearest neighbour. For :math:`k`-dimensional data (i.e. the data has :math:`k` features), a binary tree is constructed
by bisecting the data along each of the :math:`k` dimensions in sequence. The first layer bisects the data along the
first dimension, the second layer bisects each of the previous bisection results along the 2nd dimension (the data is
now partitioned into 4), and so on. The pattern repeats after the :math:`k`-th layer, until a single point of data
remains in each leaf node. A K-D-Tree that bisects data and results in each leaf node containing a single value is
called referred to as a balanced K-T-Tree.

To find the data point that is closest to a point in the tree, one descends the tree comparing the query point to the
partition value in each dimension. The final leaf node should be the closest point, however there may be a point closer
if the query point is close to a previous partition value, so some back tracking is performed to either confirm, or
update, the closest point.

A K-D-Tree can typically find the nearest neighbour in :math:`O(\log(n))` time complexity, and the data structure has
:math:`O(n)` space-complexity.

Most implementations of K-D-Tree assume that the coordinates use a cartesian geometry and therefore use a simple
Euclidean distance to identify the nearest neighbour. The implementation in ``geotrees.kdtree`` assumes a
spherical geometry on the surface of the Earth and uses the Haversine distance to identify neighbours. The
implementation has been designed to account for longitude wrapping at -180, 180 degrees. The
``geotrees.kdtree.KDTree`` class is a 2-D-Tree, the dimensions are longitude and latitude. The object is
initialised with data in the form of a list of ``geotrees.quadtree.Record`` objects. A maximum depth value
(``max_depth``) can be provided, if this is set then the partitioning will stop after ``max_depth`` partitionings,
the leaf nodes may contain more than one ``Record``.

Example
=======

.. code-block:: python

   from geotrees import KDTree, Record
   from random import choice

   lon_range = list(range(-180, 180))
   lat_range = list(range(-90, 90))
   N_samples = 1000

   records: list[Record] = [Record(choice(lon_range), choice(lat_range)) for _ in range(N_samples)]
   # Construct Tree
   kdtree = KDTree(records)

   test_value: Record = Record(lon=47.6, lat=-31.1)
   neighbours, dist = kdtree.query(test_value)

Documentation
=============

.. note:: Insertion and deletion operations may cause the ``KDTree`` to become un-balanced.

Inserting Records
-----------------

A ``Record`` can be inserted in to a ``KDTree`` with the ``KDTree.insert`` method. The method will return ``True`` if
the ``Record`` was inserted into the ``KDTree``, ``False`` otherwise. A ``Record`` will not be added if it is already
contained within the ``KDTree``, to add the ``Record`` anyway use the ``KDTree._insert`` method.

Removing Records
----------------

A ``Record`` can be removed from a ``KDTree`` with the ``KDTree.delete`` method. The method will return ``True`` if the
``Record`` was successfully removed, ``False`` otherwise (for example if the ``Record`` is not contained within the
``KDTree``).

Querying
--------

The nearest neighbour ``Record`` contained within a ``KDTree`` to a query ``Record`` can be found with the
``KDTree.query`` method. This will return a tuple containing the list of ``Record`` objects from the ``KDTree`` with
minimum distance to the query ``Record``, and the minimum distance.

kdtree Module
=============

.. automodule:: geotrees.kdtree
   :members:
