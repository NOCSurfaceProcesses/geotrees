"""Tools for fast neighbour look-up on the Earth's surface"""

from geotrees.distance_metrics import haversine
from geotrees.great_circle import GreatCircle
from geotrees.kdtree import KDTree
from geotrees.neighbours import find_nearest
from geotrees.quadtree import QuadTree
from geotrees.record import Record, SpaceTimeRecord
from geotrees.shape import (
    Ellipse,
    Rectangle,
    SpaceTimeEllipse,
    SpaceTimeRectangle,
)


__all__ = [
    "Ellipse",
    "GreatCircle",
    "KDTree",
    "QuadTree",
    "Record",
    "Rectangle",
    "SpaceTimeEllipse",
    "SpaceTimeRecord",
    "SpaceTimeRectangle",
    "find_nearest",
    "haversine",
]


__version__ = "1.0.0"
