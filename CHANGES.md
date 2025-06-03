# Changelog

## 1.0.0 (2025-06-03)

Contributors to this version: Joseph Siddons (@josidd)

### Announcements

- Module has been renamed from `GeoSpatialTools` to `geotrees` (!29)

### New features and enhancements

* `OctTree` and `QuadTree` is querying is improved by redistributing points to leaf nodes as the
  Tree is built (!33)
* `nearby_points` method for `QuadTree` and `OctTree` classes have additional `exclude_self`
  argument (!28)

### Breaking Changes

* `KDTree` `child_left` and `child_right` nodes are now `branch_left` and `branch_right` respectively (!32).
* Module renamed to `geotrees` (!29)
* Removed `SpaceTimeRecords` class, favour `list[SpaceTimeRecord]` (!27).
* `Record` and `SpaceTimeRecord` classes moved to `GeoSpatialTools.record` module (!27).
* `Rectangle`, `Ellipse`, `SpaceTimeRectangle`, `SpaceTimeEllipse` classes moved to `GeoSpatialTools.shape` module (!27).

### Internal changes

* Added notebook for `find_nearest` function (!31).
* Removed duplicate code from notebooks (!31).
* Added complete documentation (!27).
* Added CI/CD scripts for GitLab (!25).
* Added changelog (!26).

## 0.11.2 (2025-02-27)

Contributors to this version: Joseph Siddons (@josidd)

### Bug fixes

* Removed debug print statement from `OctTree.len` and `QuadTree.len` (!23).

## 0.11.1 (2025-02-26)

Contributors to this version: Joseph Siddons (@josidd)

### Bug fixes

* Fixed testing of `QuadTree.len` and `OctTree.len` - compare output only to records that are added (!21).

### Internal changes

* Removed pinned dependency version numbers (!21).

## 0.11.0 (2025-02-26)

Contributors to this version: Joseph Siddons (@josidd)

### New features and enhancements

* `QuadTree` and `OctTree` classes now have `len` method to return the number of `Record`s (!19).

## 0.10.1 (2025-02-26)

Contributors to this version: Joseph Siddons (@josidd)

### Internal changes

* Formatted and cleaned code using `ruff check` (!17).

## 0.10.0 (2024-12-12)

Contributors to this version: Joseph Siddons (@josidd)

### Internal changes

* Added documentation (!16).

## 0.9.0 (2024-12-12)

Contributors to this version: Joseph Siddons (@josidd)

### New features and enhancements

* Added `GreatCircle` class for intersecting great circles (!15)

## 0.8.0 (2024-11-27)

Contributors to this version: Joseph Siddons (@josidd)

### New features and enhancements

* `QuadTree` and `OctTree` classes now have `remove` method to remove a `Record` (!14)

## 0.7.0 (2024-11-21)

Contributors to this version: Joseph Siddons (@josidd)

### Internal changes

* Type annotations corrected to support python 3.9 (!11)

## 0.6.0 (2024-10-15)

Contributors to this version: Joseph Siddons (@josidd)

### Breaking changes

* `Rectangle` and `SpaceTimeRectangle` classes are now defined by the bounding box, rather than centre and ranges (!9).

### Bug fixes

* Account for `Rectangle` classes fully inside another `Rectangle` in intersection check.

## 0.5.0 (2024-10-10)

Contributors to this version: Joseph Siddons (@josidd)

### New features and enhancements

* Perform a second query with longitude 0 -> 360 to handle wrapping in `QuadTree` and `OctTree` classes (!8).
* Add option to fix longitude to -180 -> 180 in `Record` and `SpaceTimeRecord` classes (!8).
* Account for wrapping at -180 -> 180 in `Rectangle` and `SpaceTimeRecord` classes (!8).
* Added option to test list is sorted in `find_neighbours` (!7).

### Bug fixes

* `Rectangle` and `SpaceTimeRectangle` classes now perform an additional distance check at edges if the box crosses the equator (!8).

### Internal changes

* `Record`, `SpaceTimeRecord`, `Rectangle`, and `SpaceTimeRectangle` classes are now `dataclasses` (!8).
* `Record` and `SpaceTimeRecord` raise an error if latitude is out of bounds (!8).
* Added additional test for `KDTree` to test neighbours over the poles (!8).
* Added examples to the README (!6).

## 0.4.3 (2024-10-04)

Contributors to this version: Joseph Siddons (@josidd)

### New features and enhancements

* `KDTree` now returns a list of neighbours (!5).

### Bug fixes

* Prevent potential infinite loop in `KDTree` if multiple `Record`s have the same `lon` and `lat` (!5).
* Split `KDTree` on index rather than median (!5).

### Internal changes

* Added additional tests for `KDTree` (!5).

## 0.4.2 (2024-10-03)

Contributors to this version: Joseph Siddons (@josidd)

### Bug fixes

* Return False if query point is not in the `KDTree` (!4).
* Increment `split_index` if the next index is above the median (!4).

## 0.4.1 (2024-10-03)

Contributors to this version: Joseph Siddons (@josidd)

### New features and enhancements

* Added example notebooks.

### Bug fixes

* Account for longitude wrapping in `KDTree` class (!3).

## 0.4.0 (2024-10-03)

Contributors to this version: Joseph Siddons (@josidd)

### New features and enhancements

* `KDTree` implemented utilising haversine distances.
* `Record` and `SpaceTimeRecord` classes now have `distance` method.

## 0.3.0 (2024-09-25)

Contributors to this version: Joseph Siddons (@josidd)

### New features and enhancements

* Can now query `QuadTree` and `OctTree` objects with an `Ellipse` or `SpaceTimeEllipse` object (!2).

## 0.2.0 (2024-09-24)

Contributors to this version: Joseph Siddons (@josidd)

### New features and enhancements

* Added functions for finding nearest neighbour in a sorted 1d array (!1).

## 0.1.0 (2024-09-24)

Contributors to this version: Joseph Siddons (@josidd)

### Announcements

* Initial Release.

### New features and enhancements

* `QuadTree` and `OctTree` classes with `Record`, `Rectangle`, `SpaceTimeRecord`, `SpaceTimeRectangle` classes.
* Add haversine distance function.
