# GeoSpatialTools

Python module containing useful functions and classes for Spatial Analysis.

Tested on Python versions 3.11, 3.12, and 3.13. Not expected to work with Python 3.9 or below due
to usage of type annotations.

## Installation

As a dependency with `pip`

```bash
pip install git+ssh://git@git.noc.ac.uk/nocsurfaceprocesses/geospatialtools.git
```

## Neighbours

### 1d neighbours

For example, finding the closest time value in a list of _sorted_ time values:

```python
def find_nearest(vals: list[Numeric], test: list[Numeric]) -> list[int]:
    ...
```

Example:

```python
from GeoSpatialTools import find_nearest
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
from GeoSpatialTools import KDTree, Record
from random import choice

lon_range = list(range(-180, 180))
lat_range = list(range(-90, 90))
N_samples = 1000

records: list[Record] = [Record(choice(lon_range), choice(lat_range)) for _ in range(N_samples)]
# Construct Tree
kt = KDTree(records)

test_value: Record = Record(lon=47.6, lat=-31.1)
neighbours: list[Record] = []
neighbours, dist = kt.query(test_value)
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

Rectangle(
    lon: float,  # Centre longitude
    lat: float,  # Centre latitude
    lon_range: float,  # Full width of rectangle (degrees)
    lat_range: float,  # Full height of rectangle (degrees)
)
```

```python
from GeoSpatialTools import QuadTree, Record, Rectangle
from random import choice

lon_range = list(range(-180, 180))
lat_range = list(range(-90, 90))
N_samples = 1000

# Construct Tree
boundary = Rectangle(0, 0, 360, 180)  # Full domain
qt = QuadTree(boundary)

records: list[Record] = [Record(choice(lon_range), choice(lat_range)) for _ in range(N_samples)]
for record in records:
    qt.insert(record)

test_value: Record = Record(lon=47.6, lat=-31.1)
dist: float = 340  # km

neighbours: list[Record] = qt.nearby_points(test_value, dist)
```

#### OctTree - 3d QuadTree

Adds `SpaceTimeRecord`, `SpaceTimeRectangle` and `OctTree` classes.

```python
SpaceTimeRecord(
    lon: float,
    lat: float,
    datetime: datetime.datetime,  # datetime no longer optional
    uid: str | None,
    **data
)

SpaceTimeRectangle(
    lon: float,          # Centre longitude
    lat: float,          # Centre latitude
    datetime: datetime,  # Central datetime
    w: float,            # Full width of rectangle (degrees)
    h: float,            # Full height of rectangle (degrees)
    dt: timedelta,       # Time extent of rectangle
)
```

Example

```python
from GeoSpatialTools.octtree import OctTree, SpaceTimeRecord, SpaceTimeRectangle
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
boundary = SpaceTimeRectangle(0, 0, datetime(2009, 1, 15, 12), 360, 180, timedelta(days=31))  # Full domain
ot = OctTree(boundary)

records: list[SpaceTimeRecord] = [
    SpaceTimeRecord(choice(lon_range), choice(lat_range), choice(dates)) for _ in range(N_samples)]
for record in records:
    ot.insert(record)

test_value: SpaceTimeRecord = SpaceTimeRecord(lon=47.6, lat=-31.1, datetime=datetime(2009, 1, 23, 17, 41))
dist: float = 340  # km
t_dist = timedelta(hours=4)

neighbours: list[Record] = ot.nearby_points(test_value, dist, t_dist)
```
