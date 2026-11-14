import geopandas as gpd
import pytest
from shapely.geometry import Polygon, box

from transform.field_schema import (
    COUNTIES_PATH,
    FIELDS_PATH,
    IN_DOMAIN,
    OUT_OF_DOMAIN,
    load_fields,
    validate_fields,
)

COUNTIES = gpd.read_file(COUNTIES_PATH).set_index("county")


def _parcel(county: str, offset_m: float = 0.0) -> Polygon:
    """A 600 m square (about 36 ha) inside the county, shifted east by offset_m."""
    pt = gpd.GeoSeries([COUNTIES.geometry[county].representative_point()], crs=4326)
    x, y = pt.to_crs(5070).iloc[0].coords[0]
    square = gpd.GeoSeries([box(x + offset_m, y, x + offset_m + 600, y + 600)], crs=5070)
    return square.to_crs(4326).iloc[0]


def _row(i, role, county, note, geom=None):
    return {
        "field_id": f"{role}-{i:03d}",
        "role": role,
        "boundary_source": "demo",
        "county": county,
        "provenance": "drawn for tests",
        "domain_note": note,
        "geometry": geom or _parcel(county),
    }


def _valid_set() -> gpd.GeoDataFrame:
    rows = [_row(0, "primary", "Story", IN_DOMAIN)]
    for i in range(1, 31):
        county = "Story" if i % 2 else "Boone"
        note = OUT_OF_DOMAIN[i % 3] if i <= 6 else IN_DOMAIN
        rows.append(_row(i, "test", county, note))
    return gpd.GeoDataFrame(rows, crs=4326)


def test_valid_set_passes():
    assert validate_fields(_valid_set(), COUNTIES.reset_index()) == []


def test_self_intersecting_polygon_rejected():
    gdf = _valid_set()
    x0, y0, x1, y1 = gdf.geometry.iloc[1].bounds
    gdf.loc[1, "geometry"] = Polygon([(x0, y0), (x1, y1), (x1, y0), (x0, y1)])  # bow-tie
    assert any("invalid polygon" in e for e in validate_fields(gdf, COUNTIES.reset_index()))


def test_polygon_outside_stated_county_rejected():
    gdf = _valid_set()
    gdf.loc[1, "county"] = "Boone" if gdf.loc[1, "county"] == "Story" else "Story"
    assert any("not inside" in e for e in validate_fields(gdf, COUNTIES.reset_index()))


def test_empty_geometry_rejected():
    gdf = _valid_set()
    gdf.loc[2, "geometry"] = Polygon()
    assert any("empty" in e for e in validate_fields(gdf, COUNTIES.reset_index()))


def test_missing_property_rejected():
    gdf = _valid_set().drop(columns="provenance")
    assert any("missing properties" in e for e in validate_fields(gdf, COUNTIES.reset_index()))


def test_bad_enum_and_duplicate_id_rejected():
    gdf = _valid_set()
    gdf.loc[1, "boundary_source"] = "guess"
    gdf.loc[2, "field_id"] = gdf.loc[3, "field_id"]
    errors = validate_fields(gdf, COUNTIES.reset_index())
    assert any("boundary_source" in e for e in errors)
    assert any("field_id" in e for e in errors)


def test_set_rules_enforced():
    gdf = _valid_set().iloc[:10]  # too few test fields
    errors = validate_fields(gdf, COUNTIES.reset_index())
    assert any("at least 30 test fields" in e for e in errors)
    gdf = _valid_set()
    gdf["domain_note"] = IN_DOMAIN  # no out-of-domain fields
    assert any("out-of-domain" in e for e in validate_fields(gdf, COUNTIES.reset_index()))


def test_oversized_parcel_rejected():
    gdf = _valid_set()
    gdf.loc[1, "geometry"] = _parcel("Story").buffer(0.02)  # a few km across
    assert any("ha parcel range" in e for e in validate_fields(gdf, COUNTIES.reset_index()))


@pytest.mark.skipif(not FIELDS_PATH.exists(), reason="data/fields/fields.geojson not drawn yet")
def test_committed_field_file_is_valid():
    load_fields(FIELDS_PATH)
