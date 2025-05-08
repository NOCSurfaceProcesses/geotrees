============
Introduction
============

geotrees
===============

``geotrees`` is a python3_ library developed at NOC_ (National Oceanography Centre, Southampton, UK) for
identifying neighbours in a geo-spatial context. This is designed to solve problems where one needs to identify
data within a spatial range on the surface of the Earth. The library provides implementations of standard tools
for neighbourhood searching, such as k-d-tree_ and Quadtree_ that have been adapted to account for spherical
geometry, using a haversine_ distance metric.

The tool allows for spatial look-ups with :math:`O(\log(n))` complexity in time. Additionally, a simple 1-d nearest
neighbours look-up is provided for sorted data using bisection_ search.

``geotrees`` also provides functionality for working with great-circle_ objects, for example intersecting
great-circles.

.. include:: authors.rst

.. include:: hyperlinks.rst
