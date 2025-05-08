==============
Record Classes
==============

``Record`` classes in ``geotrees`` form the back-bone of the data structures within the library. They represent a
consistent input data-type across all classes in the library.

There are two classes of ``Record``:

* ``geotrees.record.Record`` for two-dimensional data structures defined by ``lon`` (longitude) and ``lat``
  (latitude). Optionally, one can pass ``datetime`` and ``uid``, as well as additional data attributes with keyword
  arguments.
* ``geotrees.record.SpaceTimeRecord`` for three-dimensional data structures defined by ``lon`` (longitude),
  ``lat`` (latitude), and ``datetime``. Optionally, one can pass ``uid``, as well as additional data attributes with
  keyword arguments.

Only the positional, datetime, and uid attributes are used for equality tests. ``Record`` objects are used for
``QuadTree`` and ``KDTree`` objects, whereas ``SpaceTimeRecord`` objects must be used for ``OctTree``.

.. note:: ``Record`` and ``SpaceTimeRecord`` are exposed at the ``geotrees`` level.

Example
=======

.. code-block:: python

   from geotrees import Record

   record: Record = Record(lon=-151.2, lat=42.7, uid="foo")
   dist: float = record.distance(Record(-71.1, -23.2, uid="bar"))

record Module
=============

.. automodule:: geotrees.record
   :members:
