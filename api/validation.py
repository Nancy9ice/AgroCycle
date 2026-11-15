"""Field geometry validation for POST /fields."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

COUNTY_GEOJSON = Path(__file__).resolve().parents[1] / "data" / "reference" / "story_boone_counties.geojson"
MIN_AREA_HA = 1.0
MAX_AREA_HA = 1000.0
MAX_VERTICES = 2000


def _county_union():
    from shapely.geometry import shape
    from shapely.ops import unary_union
    fc = json.loads(COUNTY_GEOJSON.read_text(encoding="utf-8"))
    return unary_union([shape(f["geometry"]) for f in fc["features"]])


def _county_name(geometry_wgs84) -> str | None:
    """Return 'Story', 'Boone', or None."""
    fc = json.loads(COUNTY_GEOJSON.read_text(encoding="utf-8"))
    from shapely.geometry import shape
    for feat in fc["features"]:
        county_shape = shape(feat["geometry"])
        if county_shape.intersects(geometry_wgs84):
            return feat["properties"]["county"]
    return None


def _area_ha(geometry_wgs84) -> float:
    from pyproj import Transformer
    from shapely.ops import transform as shp_transform
    transformer = Transformer.from_crs("EPSG:4326", "EPSG:32615", always_xy=True)
    projected = shp_transform(transformer.transform, geometry_wgs84)
    return projected.area / 10000


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

    # Vertex count
    coords = list(geom.exterior.coords) if hasattr(geom, "exterior") else []
    if len(coords) > MAX_VERTICES:
        errors.append({"code": "too_many_vertices", "message": f"Boundary has too many points ({len(coords)}). Maximum is {MAX_VERTICES}."})

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
