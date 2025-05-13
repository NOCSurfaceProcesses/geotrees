========
Quadtree
========

A Quadtree is a data-structure where each internal node has exactly four branches, and are used to recursively partition
a two-dimensional spatial domain. Each branch note is itself a Quadtree, whose spatial domain represents one of the
quadrants (north-west, north-east, south-west, south-east) of its parent's domain. The partitioning of data in this way
is dependent on the spatial density of data inserted into the Quadtree. The Quadtree is typically initialised with a
capacity value, once the capacity is reached (by inserting data points), the Quadtree divides and subsequent data points
are added to the appropriate branch-node.

Quadtree structures allow for fast identification of data within some query region. The structure of the tree ensures
that only nodes whose domain boundary intersects (or contains or is contained by) the query region are evaluated. The
time-complexity of these query operations is :math:`O(\log(n))`, the space-complexity of a Quadtree is :math:`O(n)`.

Typically, it is assumed that the data uses a cartesian coordinate system, so comparisons between boundaries and query
shapes utilise cartesian geometry and euclidean distances. The implementation of Quadtree within this library, the
``QuadTree`` class, utilises the Haversine distance as a metric for identifying records within the queried region.
This allows the Quadtree to account for the spherical geometry of the Earth. Boundary checks with query regions also
account for the wrapping of longitude at -180, 180 degrees.

The ``QuadTree`` object is defined by a bounding box, i.e. boundaries at the western, eastern, southern, and northern edges of
the data that will be inserted into the ``QuadTree``. Additionally, a capacity and maximum depth can be provided. If the
capacity is exceeded whilst inserting records the ``QuadTree`` will divide and new records will be inserted into the appropriate
branch ``QuadTree``. The maximum depth is the maximum height of the ``QuadTree``, if capacity is also specified then this will be
overridden if the ``QuadTree`` is at this depth, and the ``QuadTree`` will not divide.

Documentation
=============

Inserting Records
-----------------

A ``Record`` can be added to an ``QuadTree`` with ``QuadTree.insert`` which will return ``True`` if the operation
was successful, ``False`` otherwise. The ``QuadTree`` is modified in place.

Removing Records
----------------

A ``Record`` can be removed from an ``QuadTree`` with ``QuadTree.remove`` which will return ``True`` if the operation
was successful, ``False`` otherwise. The ``QuadTree`` is modified in place.

Querying
--------

The ``QuadTree`` class defined in ``geotrees.quadtree`` can be queried in the following ways:

* with a ``Record``, a spatial range with ``QuadTree.nearby_points``. All points within the spatial range of the
  ``Record`` will be returned in a list. The ``Record`` can be excluded from the results if the ``exclude_self``
  argument is set.
* with a ``Rectangle`` using ``QuadTree.query``. All points within the specified ``Rectangle`` will be returned in a list.
* with a ``Ellipse`` using ``QuadTree.query_ellipse``. All points within the specified ``Ellipse`` will be returned in a list.

Example
=======

.. code-block:: python

   from geotrees import QuadTree, Record, Rectangle
   from random import choice

   lon_range = list(range(-180, 180))
   lat_range = list(range(-90, 90))

   N_samples = 1000

   # Construct Tree
   boundary = Rectangle(
       west=-180,
       east=180,
       south=-90,
       north=90,
   )  # Full domain
   quadtree = QuadTree(boundary)

   # Populate the tree
   records: list[Record] = [
       Record(
           choice(lon_range),
           choice(lat_range),
       ) for _ in range(N_samples)
   ]
   for record in records:
       quadtree.insert(record)

   dist: float = 340  # km

   # Find all Records that are 340km away from test_value
   neighbours: list[Record] = quadtree.nearby_points(test_value, dist)

quadtree Module
===============

.. automodule:: geotrees.quadtree
   :members:
