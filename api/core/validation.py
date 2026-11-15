"""Field geometry validation for POST /fields."""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

COUNTY_GEOJSON = Path(__file__).resolve().parents[2] / "data" / "reference" / "story_boone_counties.geojson"
MIN_AREA_HA = 1.0
MAX_AREA_HA = 1000.0
MAX_VERTICES = 2000


@lru_cache(maxsize=1)
def _load_counties() -> list[dict]:
    """Read and cache the county GeoJSON features (called at most once per process)."""
    fc = json.loads(COUNTY_GEOJSON.read_text(encoding="utf-8"))
    return fc["features"]


def _county_name(geometry_wgs84) -> str | None:
    """Return 'Story', 'Boone', or None."""
    from shapely.geometry import shape
    for feat in _load_counties():
        if shape(feat["geometry"]).intersects(geometry_wgs84):
            return feat["properties"]["county"]
    return None


def _area_ha(geometry_wgs84) -> float:
    from pyproj import Transformer
    from shapely.ops import transform as shp_transform
    transformer = Transformer.from_crs("EPSG:4326", "EPSG:32615", always_xy=True)
    projected = shp_transform(transformer.transform, geometry_wgs84)
    return projected.area / 10000


def _vertex_count(geom) -> int:
    """Total vertex count across all rings, works for Polygon and MultiPolygon."""
    from shapely.geometry import MultiPolygon, Polygon
    if isinstance(geom, Polygon):
        return sum(len(ring.coords) for ring in [geom.exterior, *geom.interiors])
    if isinstance(geom, MultiPolygon):
        return sum(_vertex_count(p) for p in geom.geoms)
    # For other types, count coordinates generically
    return sum(1 for _ in geom.coords) if hasattr(geom, "coords") else 0


def validate_geometry(geojson_dict: dict) -> tuple[list[dict], float | None, str | None]:
    """Return (errors, area_ha, county). errors is empty on success."""
    from shapely.geometry import shape
    errors = []
    try:
        geom = shape(geojson_dict)
    except Exception:
        return [{"code": "invalid_geometry", "message": "The geometry could not be parsed."}], None, None

    if not geom.is_valid:
        return [{"code": "invalid_geometry", "message": "Boundary crosses itself or is otherwise invalid."}], None, None
    if geom.is_empty:
        return [{"code": "invalid_geometry", "message": "The boundary is empty."}], None, None

    n_vertices = _vertex_count(geom)
    if n_vertices > MAX_VERTICES:
        errors.append({"code": "too_many_vertices", "message": f"Boundary has too many points ({n_vertices}). Maximum is {MAX_VERTICES}."})

    area_ha = _area_ha(geom)
    if area_ha < MIN_AREA_HA:
        errors.append({"code": "too_small", "message": f"Field is too small ({area_ha:.1f} ha). Minimum is {MIN_AREA_HA} ha."})
    elif area_ha > MAX_AREA_HA:
        errors.append({"code": "too_large", "message": f"Field is too large ({area_ha:.0f} ha). Maximum is {MAX_AREA_HA} ha."})

    if errors:
        return errors, area_ha, None

    county = _county_name(geom)
    if county is None:
        errors.append({"code": "outside_pilot_area", "message": "AgroCycle's pilot covers Story and Boone counties, Iowa. This field is outside the pilot area."})
        return errors, area_ha, None

    return [], area_ha, county
