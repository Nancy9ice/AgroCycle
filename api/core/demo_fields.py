"""What the field map and list need beyond the repository's field record: the team's notes on each polygon
and the county outlines. Both come from files DE committed (`data/fields`, `data/reference`)."""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from shapely.geometry import shape

ROOT = Path(__file__).resolve().parents[2]
FIELDS_PATH = ROOT / "data" / "fields" / "fields.geojson"
COUNTIES_PATH = ROOT / "data" / "reference" / "story_boone_counties.geojson"


@lru_cache(maxsize=1)
def field_notes() -> dict[str, dict]:
    """Per field: provenance, domain note, cover detail and centroid (lon, lat)."""
    notes = {}
    for feature in json.loads(FIELDS_PATH.read_text(encoding="utf-8"))["features"]:
        props = feature["properties"]
        centroid = shape(feature["geometry"]).centroid
        notes[props["field_id"]] = {
            "provenance": props.get("provenance") or "",
            "domain_note": props.get("domain_note") or "",
            "cover_detail": props.get("cover_detail"),
            "centroid": [round(centroid.x, 6), round(centroid.y, 6)],
        }
    return notes


@lru_cache(maxsize=1)
def pilot_counties() -> list[dict]:
    """The Story and Boone outlines as one closed ring each: [{county, ring: [[lon, lat], ...]}]."""
    out = []
    for feature in json.loads(COUNTIES_PATH.read_text(encoding="utf-8"))["features"]:
        out.append({"county": feature["properties"]["county"], "ring": feature["geometry"]["coordinates"][0]})
    return out
