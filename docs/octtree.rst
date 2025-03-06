=======
OctTree
=======

An Octtree is an extension of the Quadtree into a third dimension. In standard Octtree implementations the third
dimension is treated as another spatial dimension, in that distance checks are performed using Euclidean distances.
Here, the third dimension is considered to be a time dimension. Any look-ups using the Octtree require a timedelta to be
provided, so that any records falling within the spatial range are returned only if they also fall within the time range
defined by the timedelta.

Whilst the Quadtree divides into 4 children after the capacity is reached, the Octtree divides into 8 children. The
divisions are at the longitude midpoint, the latitude midpoint, and the datetime midpoint of the boundary.

The ``OctTree`` class defined in ``GeoSpatialTools.octtree`` can be queried in the following ways:

* with a ``SpaceTimeRecord``, a spatial range, and a time range (specified by a ``datetime.timedelta``) with 
  ``OctTree.nearby_points``. All points within the spatial range and time range of the ``SpaceTimeRecord`` will be
  returned in a list.
* with a ``SpaceTimeRectangle``. All points within the specified ``SpaceTimeRectangle`` will be returned in a list.
* with a ``SpaceTimeEllipse``. All points within the specified ``SpaceTimeEllipse`` will be returned in a list.

Example
-------

.. code-block:: python

   from GeoSpatialTools.octtree import OctTree, SpaceTimeRecord, SpaceTimeRectangle
   from datetime import datetime, timedelta
   from random import choice
   from polars import datetime_range

   lon_range = list(range(-180, 180))
   lat_range = list(range(-90, 90))

   dates = date_range(
       start=datetime(2009, 1, 1, 0, 0),
       end=datetime(2009, 2, 1, 0, 0),
       interval=timedelta(hours=1),
       closed="left",
       eager=True,
   )
   N_samples = 1000

   # Construct Tree
   boundary = SpaceTimeRectangle(
       west=-180,
       east=180,
       south=-90,
       north=90,
       start=datetime(2009, 1, 1, 0),
       end=datetime(2009, 1, 2, 23),
   )  # Full domain
   octtree = OctTree(boundary)

   # Populate the tree
   records: list[SpaceTimeRecord] = [
       SpaceTimeRecord(
           choice(lon_range),
           choice(lat_range),
           choice(dates)
       ) for _ in range(N_samples)
   ]
   for record in records:
       octtree.insert(record)

   test_value: SpaceTimeRecord = SpaceTimeRecord(
       lon=47.6, lat=-31.1, datetime=datetime(2009, 1, 23, 17, 41)
   )
   dist: float = 340  # km
   t_dist = timedelta(hours=4)

   # Find all Records that are 340km away from test_value, and within 4 hours
   # of test_value
   neighbours: list[SpaceTimeRecord] = octtree.nearby_points(
       test_value, dist, t_dist
   )

octtree Module
--------------

.. automodule:: GeoSpatialTools.octtree
   :members:
