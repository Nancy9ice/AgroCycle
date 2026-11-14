"""Subsets of the demo fields: what to request from each source, and the size budget.

Buffers are applied in EPSG:5070 (metres) and results are returned in EPSG:4326
(lon/lat) unless the name says otherwise.
"""

import geopandas as gpd

from transform.field_schema import COUNTIES_PATH

AREA_CRS = 5070
Bbox = tuple[float, float, float, float]  # minx, miny, maxx, maxy


class SizeBudgetExceededError(RuntimeError):
    """A pull is larger than the budget set for its source."""


def _round(values, digits: int = 6) -> tuple[float, ...]:
    return tuple(round(float(v), digits) for v in values)


def field_bboxes(fields: gpd.GeoDataFrame, buffer_m: float = 0.0) -> dict[str, Bbox]:
    """One bbox per field, grown by buffer_m metres on every side."""
    grown = fields.set_index("field_id").to_crs(AREA_CRS).geometry.buffer(buffer_m)
    return {fid: _round(g.bounds) for fid, g in grown.to_crs(4326).items()}


def union_bbox(fields: gpd.GeoDataFrame, buffer_m: float = 0.0) -> Bbox:
    """One bbox that covers every field plus the buffer."""
    grown = fields.to_crs(AREA_CRS).geometry.buffer(buffer_m)
    return _round(grown.to_crs(4326).total_bounds)


def field_points(fields: gpd.GeoDataFrame) -> dict[str, tuple[float, float]]:
    """A point inside each field (lon, lat), for gridded or point-based sources."""
    inside = fields.set_index("field_id").to_crs(AREA_CRS).geometry.representative_point()
    return {fid: _round((p.x, p.y)) for fid, p in inside.to_crs(4326).items()}


def county_bboxes(buffer_m: float = 0.0) -> dict[str, Bbox]:
    """County bboxes in EPSG:5070 (the CDL grid), for county-level clips."""
    counties = gpd.read_file(COUNTIES_PATH).set_index("county").to_crs(AREA_CRS)
    return {name: _round(g.buffer(buffer_m).bounds, 1) for name, g in counties.geometry.items()}


def subset_record(kind: str, **params) -> dict:
    """The dict stored in a manifest's `subset` field."""
    return {"kind": kind, **params}


def check_budget(source: str, total_bytes: int, cap_bytes: int) -> None:
    if total_bytes > cap_bytes:
        raise SizeBudgetExceededError(
            f"{source}: {total_bytes / 1e6:.1f} MB is over the {cap_bytes / 1e6:.1f} MB budget"
        )
