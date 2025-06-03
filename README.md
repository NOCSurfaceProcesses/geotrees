# GeoTrees

Python module containing useful functions and classes for Spatial Analysis.

Tested on Python versions 3.9 to 3.13.

## Installation

As a dependency with `pip`

```bash
pip install geotrees
```

The only dependency of the library is `numpy`. Optional dependencies required to run the example
notebooks are `ipykernel` and `polars`.

## Neighbours

### 1d neighbours

For example, finding the closest time value in a list of _sorted_ time values:

```python
def find_nearest(vals: list[Numeric], test: list[Numeric]) -> list[int]:
    ...
```

Example:

```python
from geotrees import find_nearest
import numpy as np

# Generate random neighbours and test points
potential_neighbours = list(np.random.randn(100))
potential_neighbours.sort()
test_values = list(np.random.randn(3))

neighbour_i = find_nearest(potential_neighbours, test_values)
```

Returns the index of the value in `potential_neighbours` that is closest to each value in
`test_values`. This function makes use of `bisect.bisect` from the python standard library and
requires that the list `potential_neighbours` is sorted. No check on sorted-ness is performed, if
the list is unsorted then the incorrect answer will be returned.

This calculation is performed in `O(log(n))` time.

### 2d neighbours

An implementation of `KDTree` (specifically a `2DTree`) using Haversine distance as the query
distance and accounting for longitudinal wrapping at -180, 180.

Uses a `Record` class:

```python
Record(
    lon: float,
    lat: float,
    datetime: datetime.datetime | None,
    uid: str | None,
    **data
)
```

Fast look-up of nearest neighbours in 2 spatial dimensions (longitude and latitude).

```python
KDTree(
    points: list[Record],
    max_depth: int,
    depth: int = 0  # Internal parameter
)
```

```python
from geotrees import KDTree, Record
from random import choice

lon_range = list(range(-180, 180))
lat_range = list(range(-90, 90))
N_samples = 1000

records: list[Record] = [Record(choice(lon_range), choice(lat_range)) for _ in range(N_samples)]
# Construct Tree
kdtree = KDTree(records)

test_value: Record = Record(lon=47.6, lat=-31.1)
neighbours: list[Record] = []
neighbours, dist = kdtree.query(test_value)
```

### Points within distance (2d \& 3d)

Also included is an implementation of `QuadTree` and `OctTree` using Haversine distance for querying
with a test `Record` and distance.

```python
QuadTree(
    boundary: Rectangle,
    capacity: int,
    max_depth: int,
    depth: int = 0  # Internal parameter
)
```

The boundary is defined by a `Rectangle` class, which is defined by the bounding box.

```python
Rectangle(
    west: float,   # Western edge
    east: float,   # Eastern edge
    south: float,  # Southern edge
    north: float,  # Northern edge
)
```

The `Rectangle` class will raise an error if the northern or southern boundary go beyond the north
or south pole.

```python
from geotrees import QuadTree, Record, Rectangle
from random import choice

lon_range = list(range(-180, 180))
lat_range = list(range(-90, 90))
N_samples = 1000

# Construct Tree
boundary = Rectangle(-180, 180, -90, 90)  # Full domain
quadtree = QuadTree(boundary)

records: list[Record] = [Record(choice(lon_range), choice(lat_range)) for _ in range(N_samples)]
for record in records:
    quadtree.insert(record)

test_value: Record = Record(lon=47.6, lat=-31.1)
dist: float = 340  # km

neighbours: list[Record] = quadtree.nearby_points(test_value, dist)
```

#### OctTree - 3d QuadTree

Adds `SpaceTimeRecord`, `SpaceTimeRectangle` and `OctTree` classes. This allows for querying in a
third dimension, specifically this adds a time dimension. Typically the time dimension is assumed
to be of `datetime.datetime` type, however this is expected to work with numeric values, for example
pentad, day of year. However, this non-datetime behaviour is not intended.

```python
SpaceTimeRecord(
    lon: float,
    lat: float,
    datetime: datetime.datetime,  # datetime no longer optional
    uid: str | None,
    **data
)
```

As with the `Rectangle` class for the `QuadTree`, the `SpaceTimeRectangle` defines the boundary of
an `OctTree` class, and is defined by the space-time bounding box.

```python
SpaceTimeRectangle(
    west: float,               # Western edge
    east: float,               # Eastern edge
    south: float,              # Southern edge
    north: float,              # Northern edge
    start: datetime.datetime,  # Start datetime
    end: datetime.datetime,    # End datetime
)
```

Example

```python
from geotrees import OctTree, SpaceTimeRecord, SpaceTimeRectangle
from datetime import datetime, timedelta
from random import choice
from pandas import date_range

lon_range = list(range(-180, 180))
lat_range = list(range(-90, 90))

dates = date_range(
    start=datetime(2009, 1, 1, 0, 0),
    end=datetime(2009, 2, 1, 0, 0),
    interval=timedelta(hours=1),
    inclusive="left",
)
N_samples = 1000

# Construct Tree
boundary = SpaceTimeRectangle(-180, 180, -90, 90, datetime(2009, 1, 1, 0), datetime(2009, 1, 2, 23))  # Full domain
octtree = OctTree(boundary)

records: list[SpaceTimeRecord] = [
    SpaceTimeRecord(choice(lon_range), choice(lat_range), choice(dates)) for _ in range(N_samples)]
for record in records:
    octtree.insert(record)

test_value: SpaceTimeRecord = SpaceTimeRecord(lon=47.6, lat=-31.1, datetime=datetime(2009, 1, 23, 17, 41))
dist: float = 340  # km
t_dist = timedelta(hours=4)

neighbours: list[Record] = octtree.nearby_points(test_value, dist, t_dist)
```
