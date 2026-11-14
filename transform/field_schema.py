"""Schema and geometry checks for the demo field polygons (data/fields/fields.geojson).

Run directly to validate a file:  uv run python -m transform.field_schema [path]
"""

import sys
from pathlib import Path

import geopandas as gpd
import pandas as pd
import pandera.pandas as pa

ROOT = Path(__file__).resolve().parent.parent
FIELDS_PATH = ROOT / "data" / "fields" / "fields.geojson"
COUNTIES_PATH = ROOT / "data" / "reference" / "story_boone_counties.geojson"

ROLES = ["primary", "test"]
BOUNDARY_SOURCES = ["demo", "real"]
COUNTIES = ["Story", "Boone"]
IN_DOMAIN = "in-domain: maize-soybean rotation"
OUT_OF_DOMAIN = [
    "out-of-domain: continuous corn",
    "out-of-domain: pasture-hay",
    "out-of-domain: mixed-non-rotation",
]
DOMAIN_NOTES = [IN_DOMAIN, *OUT_OF_DOMAIN]

MIN_TEST_FIELDS = 30
MIN_OUT_OF_DOMAIN = 3
MIN_AREA_HA = 4.0
MAX_AREA_HA = 260.0
AREA_CRS = "EPSG:5070"  # NAD83 / Conus Albers, equal-area, metres

properties_schema = pa.DataFrameSchema(
    {
        "field_id": pa.Column(str, unique=True, nullable=False),
        "role": pa.Column(str, pa.Check.isin(ROLES), nullable=False),
        "boundary_source": pa.Column(str, pa.Check.isin(BOUNDARY_SOURCES), nullable=False),
        "county": pa.Column(str, pa.Check.isin(COUNTIES), nullable=False),
        "provenance": pa.Column(str, pa.Check.str_length(min_value=1), nullable=False),
        "domain_note": pa.Column(str, pa.Check.isin(DOMAIN_NOTES), nullable=False),
    },
    strict=False,
    coerce=False,
)


def _property_errors(gdf: gpd.GeoDataFrame) -> list[str]:
    missing = [c for c in properties_schema.columns if c not in gdf.columns]
    if missing:
        return [f"missing properties: {', '.join(missing)}"]
    try:
        properties_schema.validate(pd.DataFrame(gdf.drop(columns="geometry")), lazy=True)
    except pa.errors.SchemaErrors as err:
        return [
            f"properties: {row.column} {row.check} (field_id={_field_id(gdf, row.index)})"
            for row in err.failure_cases.itertuples()
        ]
    return []


def _field_id(gdf: gpd.GeoDataFrame, index) -> str:
    try:
        return str(gdf.loc[int(index), "field_id"])
    except (TypeError, ValueError, KeyError):
        return "n/a"


def _geometry_errors(gdf: gpd.GeoDataFrame, counties: gpd.GeoDataFrame) -> list[str]:
    errors = []
    if gdf.crs is None or gdf.crs.to_epsg() != 4326:
        return ["CRS must be EPSG:4326 (WGS84)"]
    county_geom = counties.set_index("county").geometry
    areas_ha = gdf.to_crs(AREA_CRS).geometry.area / 10_000
    for i, row in gdf.iterrows():
        fid, geom = row.get("field_id", f"row {i}"), row.geometry
        if geom is None or geom.is_empty:
            errors.append(f"{fid}: geometry is empty")
        elif geom.geom_type != "Polygon":
            errors.append(f"{fid}: geometry must be a Polygon, got {geom.geom_type}")
        elif not geom.is_valid:
            errors.append(f"{fid}: invalid polygon (e.g. self-intersection)")
        else:
            county = row.get("county")
            if county in county_geom.index and not county_geom[county].contains(geom):
                errors.append(f"{fid}: not inside {county} County")
            if not MIN_AREA_HA <= areas_ha[i] <= MAX_AREA_HA:
                errors.append(
                    f"{fid}: area {areas_ha[i]:.1f} ha outside "
                    f"{MIN_AREA_HA:g}-{MAX_AREA_HA:g} ha parcel range"
                )
    return errors


def _set_errors(gdf: gpd.GeoDataFrame) -> list[str]:
    errors = []
    n_primary = int((gdf["role"] == "primary").sum())
    n_test = int((gdf["role"] == "test").sum())
    if n_primary != 1:
        errors.append(f"expected exactly 1 primary field, found {n_primary}")
    if n_test < MIN_TEST_FIELDS:
        errors.append(f"expected at least {MIN_TEST_FIELDS} test fields, found {n_test}")
    for county in COUNTIES:
        if not (gdf["county"] == county).any():
            errors.append(f"no fields in {county} County")
    n_out = int(gdf["domain_note"].isin(OUT_OF_DOMAIN).sum())
    if n_out < MIN_OUT_OF_DOMAIN:
        errors.append(f"expected at least {MIN_OUT_OF_DOMAIN} out-of-domain fields, found {n_out}")
    primary = gdf[gdf["role"] == "primary"]
    if (primary["domain_note"] != IN_DOMAIN).any():
        errors.append("the primary field must be in-domain (maize-soybean rotation)")
    return errors


def validate_fields(
    gdf: gpd.GeoDataFrame,
    counties: gpd.GeoDataFrame | None = None,
    check_set: bool = True,
) -> list[str]:
    """Return a list of human-readable problems; an empty list means valid."""
    errors = _property_errors(gdf)
    if errors:
        return errors
    if counties is None:
        counties = gpd.read_file(COUNTIES_PATH)
    errors += _geometry_errors(gdf, counties)
    if check_set:
        errors += _set_errors(gdf)
    return errors


def load_fields(path: Path = FIELDS_PATH) -> gpd.GeoDataFrame:
    """Read and validate the field file; raise ValueError listing every problem."""
    gdf = gpd.read_file(path)
    errors = validate_fields(gdf)
    if errors:
        raise ValueError("Invalid field file:\n- " + "\n- ".join(errors))
    return gdf


def main() -> int:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else FIELDS_PATH
    try:
        gdf = load_fields(path)
    except ValueError as err:
        print(err)
        return 1
    print(f"OK: {len(gdf)} fields valid")
    print(gdf.groupby(["county", "domain_note"]).size().to_string())
    return 0


if __name__ == "__main__":
    sys.exit(main())
