.. module:: GeoSpatialTools

.. PyCOADS documentation master file, created by
   sphinx-quickstart on Fri Jul  5 11:49:36 2024.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

``GeoSpatialTools`` documentation
---------------------------------

``GeoSpatialTools`` is a python3_ library for identifying neighbours in a geo-spatial context. This is designed to solve
problems where one needs to identify data within a spatial range on the surface of the Earth. The library provides
implementations of standard tools for neighbourhood searching, such as k-d-tree_ and Quadtree_ that have been
adapted to account for spherical geometry, using a haversine_ distance metric. 

The tool allows for spatial look-ups with :math:`O(\log(n))` complexity in time. Additionally, a simple 1-d nearest
neighbours look-up is provided for sorted data using bisection_ search.

``GeoSpatialTools`` also provides functionality for working with great-circle_ objects, for example intersecting
great-circles.

.. toctree::
   :maxdepth: 4
   :caption: Contents:
    
   authors
   installation
   quadtree
   octtree
   users_guide

   
.. include:: hyperlinks.rst

..
.. Indices and tables
.. ------------------
..
.. * :ref:`genindex`
.. * :ref:`modindex`
.. * :ref:`search`

