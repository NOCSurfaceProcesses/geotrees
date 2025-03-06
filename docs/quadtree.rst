========
Quadtree
========

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

The ``QuadTree`` class defined in ``GeoSpatialTools.quadtree`` can be queried in the following ways:

* with a ``Record``, a spatial range with ``QuadTree.nearby_points``. All points within the spatial range of the
  ``Record`` will be returned in a list.
* with a ``Rectangle`` using ``QuadTree.query``. All points within the specified ``Rectangle`` will be returned in a list.
* with a ``Ellipse`` using ``QuadTree.query_ellipse``. All points within the specified ``Ellipse`` will be returned in a list.

Example
=======

.. code-block:: python

   from GeoSpatialTools.quadtree import QuadTree, Record, Rectangle
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

.. automodule:: GeoSpatialTools.quadtree
   :members:
