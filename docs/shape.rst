=============
Shape Classes
=============

The ``geotrees.shape`` module defines various classes that can be used to define the boundary for ``QuadTree``
and ``OctTree`` classes, or query regions for the same.

``Rectangle`` and ``SpaceTimeRectangle`` classes are used to define the boundaries for ``QuadTree`` and ``OctTree``
classes respectively. They are defined by the bounding box in space (and time for a ``SpaceTimeRectangle``).

``Ellipse`` and ``SpaceTimeEllipse`` classes are defined by ``lon`` and ``lat`` indicating the centre of the ellipse, ``a``
and ``b`` indicating the length of the semi-major and semi-minor axes respectively, and ``theta`` indicating the angle
of the ellipse. ``SpaceTimeEllipse`` classes also require ``start`` and ``end`` datetime values. The
``SpaceTimeEllipse`` is an elliptical cylinder where the height is represented by the time dimension.

``Rectangle`` and ``Ellipse`` classes can be used to define a query shape for a ``QuadTree``, using ``QuadTree.query``
and ``QuadTree.query_ellipse`` respectively.

``SpaecTimeRectangle`` and ``SpaceTimeEllipse`` classes can be used to define a query shape for a ``OctTree``, using
``OctTree.query`` and ``OctTree.query_ellipse`` respectively.

Example
=======

.. code-block:: python

   from geotrees.shape import Rectangle, SpaceTimeEllipse
   from datetime import datetime
   from math import pi

   rectangle: Rectangle = Rectangle(
       west=-180,
       east=180,
       south=-90,
       north=90,
   )

   ellipse: SpaceTimeEllipse = SpaceTimeEllipse(
       lon=23.4,
       lat=-17.9,
       a=103,
       b=71,
       theta=pi/3,
       start=datetime(2009, 2, 13, 19, 30),
       end=datetime(2010, 7, 2, 3, 45),
   )

shape Module
============

.. automodule:: geotrees.shape
   :members:
