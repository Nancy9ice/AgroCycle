"""The tracked dev sample loads, matches its manifest, and agrees with the committed field data."""

import hashlib
import json
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import pytest
import rasterio
from rasterio.features import geometry_mask
from shapely import wkt

ROOT = Path(__file__).resolve().parent.parent
SAMPLE = ROOT / "data" / "sample"
FIELD_DIR = SAMPLE / "primary-001"
CLEAR_BITS = 0b00111110

pytestmark = pytest.mark.skipif(not (SAMPLE / "sample_manifest.json").exists(), reason="no dev sample")


@pytest.fixture(scope="module")
def manifest():
    return json.loads((SAMPLE / "sample_manifest.json").read_text())


@pytest.fixture(scope="module")
def field():
    return gpd.read_file(ROOT / "data/fields/fields.geojson").set_index("field_id").geometry["primary-001"]


def test_every_listed_file_exists_and_matches_its_hash(manifest):
    assert len(manifest["files"]) == 48
    for entry in manifest["files"]:
        path = FIELD_DIR / entry["path"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == entry["sample_sha256"], entry["path"]
        assert entry["derived_from"].startswith("raw/") and len(entry["source_sha256"]) == 64
    on_disk = {str(p.relative_to(FIELD_DIR)) for p in FIELD_DIR.rglob("*") if p.is_file()}
    assert on_disk == {e["path"] for e in manifest["files"]}  # nothing unlisted


def test_the_sample_is_small():
    total = sum(p.stat().st_size for p in SAMPLE.rglob("*") if p.is_file())
    assert total < 1_000_000


def test_cdl_windows_reproduce_the_committed_crop_sequence_of_the_primary_field(field):
    notes = pd.read_csv(ROOT / "data/fields/field_selection_notes.csv").set_index("field_id")
    expected = notes.loc["primary-001", "crops_2015_2025"]
    letters = ""
    for year in range(2015, 2026):
        with rasterio.open(FIELD_DIR / "cdl" / f"CDL_{year}_19169_window.tif") as src:
            assert src.crs.to_epsg() == 5070 and src.res == (30.0, 30.0)
            geom = gpd.GeoSeries([field], crs=4326).to_crs(src.crs).iloc[0]
            inside = geometry_mask([geom], out_shape=src.shape, transform=src.transform, invert=True)
            codes, counts = np.unique(src.read(1)[inside], return_counts=True)
        letters += {1: "C", 5: "S"}.get(int(codes[counts.argmax()]), "?")
    assert letters == expected == "SCSCSCSCSCS"


@pytest.mark.parametrize("sensor,bands", [("l30", ("b04", "b05", "b06", "fmask")), ("s30", ("b04", "b8a", "b11", "fmask"))])
def test_hls_scenes_have_the_right_bands_and_are_clear(sensor, bands, field):
    days = sorted(p.name for p in (FIELD_DIR / "hls" / sensor).iterdir())
    assert len(days) == 4 and all(d.startswith("2023") for d in days)
    for day in days:
        assert sorted(p.stem for p in (FIELD_DIR / "hls" / sensor / day).glob("*.tif")) == sorted(bands)
        with rasterio.open(FIELD_DIR / "hls" / sensor / day / "fmask.tif") as fm:
            assert fm.crs.to_epsg() == 32615 and fm.dtypes[0] == "uint8"
            geom = gpd.GeoSeries([field], crs=4326).to_crs(fm.crs).iloc[0]
            inside = geometry_mask([geom], out_shape=fm.shape, transform=fm.transform, invert=True)
            clear = inside & ((fm.read(1) & CLEAR_BITS) == 0)
        assert clear.sum() / inside.sum() >= 0.99
        for band in bands[:3]:
            with rasterio.open(FIELD_DIR / "hls" / sensor / day / f"{band}.tif") as src:
                assert src.dtypes[0] == "int16" and src.nodata == -9999
                values = src.read(1)[clear] * 0.0001
            assert 0 < values.min() and values.max() < 1.0, (sensor, day, band)


def test_power_season_has_seven_variables_and_a_full_2023_without_fill_values(manifest):
    doc = json.loads((FIELD_DIR / "power" / "primary-001_20230101-20231231.json").read_text())
    parameter = doc["properties"]["parameter"]
    assert set(parameter) == {"T2M_MAX", "T2M_MIN", "T2M", "PRECTOTCORR", "RH2M", "ALLSKY_SFC_SW_DWN", "WS2M"}
    for series in parameter.values():
        assert len(series) == 365 and all(d.startswith("2023") for d in series)
        assert -999.0 not in series.values()
    assert doc["header"]["fill_value"] == -999.0 and doc["header"]["time_standard"] == "LST"


def test_ssurgo_responses_are_consistent_with_each_other(field):
    def table(name):
        return json.loads((FIELD_DIR / "ssurgo" / name).read_text())["Table"]

    a, b, c = table("step_a_map_units.json"), table("step_b_components.json"), table("step_c_horizons.json")
    area = gpd.GeoSeries([field], crs=4326).to_crs(5070).area.iloc[0]
    shares = {}
    for mukey, geometry in a[1:]:
        piece = gpd.GeoSeries([wkt.loads(geometry)], crs=4326).to_crs(5070).area.iloc[0]
        shares[mukey] = shares.get(mukey, 0) + piece / area
    assert len(shares) == 10 and sum(shares.values()) == pytest.approx(1.0, abs=0.01)
    pct = {}
    for row in b[1:]:
        pct[row[0]] = pct.get(row[0], 0) + int(row[5])
    assert set(pct) == set(shares) and all(v == 100 for v in pct.values())
    assert all(float(r[3]) < float(r[4]) for r in c[1:])  # horizon top above bottom
