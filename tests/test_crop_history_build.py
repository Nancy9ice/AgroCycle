"""Zonal counting and the frame builders: synthetic rasters, the committed dev sample, and (when the
raw clips are on this machine) the real data."""

from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import pandera.errors
import pytest
import rasterio
import shapely
from rasterio.transform import from_origin
from shapely.geometry import box

from common.schemas import CROP_CLASS_SHARES, CROP_HISTORY, CROP_ROTATION, FIELDS
from ingest.cdl import default_dir
from transform.crop_history import build, rules, zonal
from transform.field_schema import FIELDS_PATH, load_fields

SAMPLE = Path(__file__).resolve().parent.parent / "data" / "sample" / "primary-001" / "cdl"
CLIPS_PRESENT = any(default_dir().glob("polygonclip_*/CDL_2015_19169.tif"))
SCHEMA_ERRORS = (pandera.errors.SchemaError, pandera.errors.SchemaErrors)


def write_raster(path, data, origin=(0.0, 300.0), crs="EPSG:5070"):
    with rasterio.open(path, "w", driver="GTiff", height=data.shape[0], width=data.shape[1], count=1,
                       dtype="uint8", crs=crs, transform=from_origin(*origin, 30, 30)) as out:
        out.write(data.astype("uint8"), 1)


@pytest.fixture
def grid(tmp_path):
    """10 x 10 pixels, 30 m: columns 0-4 corn (1), columns 5-9 soybeans (5); row 0 is no data (0)."""
    data = np.where(np.arange(10)[None, :] < 5, 1, 5) * np.ones((10, 1), dtype=int)
    data[0, :] = 0
    path = tmp_path / "grid.tif"
    write_raster(path, data)
    return path


def test_counts_use_pixels_whose_centre_is_inside(grid):
    # x 60-150 m and y 120-210 m (the raster's top edge is y = 300): columns 2-4, rows 3-5 -> 9 corn pixels
    assert zonal.field_counts(grid, box(60, 120, 150, 210)) == {1: 9}
    # column 4's centre is x = 135 and column 5's is x = 165: a box ending at 164 holds one column of 3 pixels,
    # and ending at 166 it holds both
    assert zonal.field_counts(grid, box(120, 120, 164, 210)) == {1: 3}
    assert zonal.field_counts(grid, box(120, 120, 166, 210)) == {1: 3, 5: 3}


def test_a_field_spanning_corn_soybeans_and_no_data(grid):
    counts = zonal.field_counts(grid, box(120, 240, 180, 300))  # rows 0-1, columns 4-5
    assert counts == {0: 2, 1: 1, 5: 1}  # row 0 is no data; columns 4-5, rows 0-1 = 4 pixels


def test_a_field_outside_the_clip_or_in_the_wrong_crs_is_refused(grid, tmp_path):
    with pytest.raises(ValueError, match="not inside"):
        zonal.field_counts(grid, box(-100, 0, 100, 100))
    wrong = tmp_path / "wrong.tif"
    write_raster(wrong, np.ones((4, 4)), crs="EPSG:32615")
    with pytest.raises(ValueError, match="CRS"):
        zonal.field_counts(wrong, box(0, 200, 60, 280))


def centre_counts(raster, geometry):
    """An independent count: test each pixel centre with shapely, no rasterize call."""
    with rasterio.open(raster) as src:
        data, tf = src.read(1), src.transform
    rows, cols = np.indices(data.shape)
    xs, ys = tf @ (cols + 0.5, rows + 0.5)
    inside = shapely.contains_xy(geometry, xs, ys)
    codes, counts = np.unique(data[inside], return_counts=True)
    return dict(zip(codes.tolist(), counts.tolist(), strict=True))


def test_the_primary_field_from_the_dev_sample_matches_an_independent_count_every_year():
    gdf = load_fields()
    primary = gdf[gdf["field_id"] == "primary-001"].to_crs(zonal.RASTER_CRS).geometry.iloc[0]
    labels = {}
    for tif in sorted(SAMPLE.glob("CDL_*_19169_window.tif")):
        year = int(tif.name.split("_")[1])
        counts = zonal.field_counts(tif, primary)
        assert dict(counts) == centre_counts(tif, primary), year
        labels[year] = rules.label_year(counts)
    assert sorted(labels) == list(range(2015, 2026))
    result = rules.classify_field(labels)  # DS1's own worked example for the primary field
    assert result.sequence == "S C S C S C S C S C S"
    assert (result.field_class, result.alternations) == ("rotation", 10)


def fake_clips(counties=("Story", "Boone")):
    return {
        (county, year): zonal.Clip(county, year, Path(f"CDL_{year}.tif"), 30, f"CDL {year}",
                                   f"raw/cdl/v/2026-11-14/CDL_{year}_{county}.tif")
        for county in counties for year in range(2015, 2026)
    }


@pytest.fixture
def stubbed(monkeypatch):
    """crop_frames with canned counts: corn and soybeans alternate by year, soybeans first (S in 2015)."""
    monkeypatch.setattr(zonal, "class_names", lambda path: {0: "Background", 1: "Corn", 5: "Soybeans", 27: "Rye"})

    def counter(path, geometry):
        year = int(path.stem.split("_")[1])
        return {5: 60, 1: 30, 27: 10} if year % 2 else {1: 60, 5: 30, 27: 10}

    gdf = gpd.read_file(FIELDS_PATH).head(3)
    return build.crop_frames(gdf, fake_clips(), counter), gdf


def test_frames_have_one_row_per_field_year_and_pass_their_schemas(stubbed):
    crops, _ = stubbed
    assert len(crops.history) == 3 * 11 and len(crops.rotation) == 3
    CROP_CLASS_SHARES.validate(crops.shares)
    CROP_HISTORY.validate(crops.history)
    CROP_ROTATION.validate(crops.rotation)


def test_shares_sum_to_100_per_field_year(stubbed):
    crops, _ = stubbed
    sums = crops.shares.groupby(["field_id", "year"])["share_pct"].sum()
    assert np.allclose(sums, 100)


def test_every_row_carries_the_rule_version_provenance_and_a_limitation(stubbed):
    crops, _ = stubbed
    assert set(crops.history["rule_version"]) == {rules.RULE_VERSION}
    assert set(crops.rotation["rule_version"]) == {rules.RULE_VERSION}
    assert crops.rotation["limitation"].str.contains("not ground truth").all()
    assert (crops.shares["resolution_m"] == 30).all() and crops.shares["source_s3_key"].str.startswith("raw/cdl/").all()
    assert set(crops.history["evidence_type"]) == {"classified"} and set(crops.rotation["evidence_type"]) == {"derived"}


def test_an_unlisted_code_is_kept_flagged_and_reported(stubbed):
    crops, _ = stubbed
    rye = crops.shares[crops.shares["cdl_class_code"] == 27]
    assert (rye["flag"] == "unlisted_code").all() and (rye["class_group"] == "other_crop").all()
    assert crops.unlisted_codes == {27: "Rye"}


def test_each_field_is_counted_only_in_its_own_county_clips(stubbed):
    crops, _ = stubbed
    assert crops.history.groupby("field_id")["year"].nunique().eq(11).all()


def test_a_mixed_label_and_a_class_reach_the_rotation_row(monkeypatch):
    monkeypatch.setattr(zonal, "class_names", lambda path: {1: "Corn", 5: "Soybeans"})
    gdf = gpd.read_file(FIELDS_PATH).head(1)
    crops = build.crop_frames(gdf, fake_clips(), lambda p, g: {1: 50, 5: 50})
    assert set(crops.history["status"]) == {"mixed_uncertain"}
    assert crops.rotation["sequence"].iloc[0].replace(" ", "") == "M" * 11
    assert crops.rotation["field_class"].iloc[0] == "other"


def test_the_45_demo_fields_become_a_valid_fields_frame():
    frame = build.fields_frame(load_fields())
    assert len(FIELDS.validate(frame)) == 45
    assert set(frame["boundary_source"]) == {"demo"} and (frame["role"] == "primary").sum() == 1


def test_a_bad_status_or_missing_limitation_is_rejected(stubbed):
    crops, _ = stubbed
    with pytest.raises(SCHEMA_ERRORS):
        CROP_HISTORY.validate(crops.history.assign(status="great"))
    with pytest.raises(SCHEMA_ERRORS):
        CROP_ROTATION.validate(crops.rotation.assign(limitation=""))
    with pytest.raises(SCHEMA_ERRORS):
        CROP_CLASS_SHARES.validate(pd.concat([crops.shares, crops.shares.head(1)], ignore_index=True))  # duplicate key


@pytest.mark.skipif(not CLIPS_PRESENT, reason="the CDL clips are not on this machine (DE only)")
def test_real_clips_agree_with_an_independent_count_for_one_field_per_class():
    gdf = load_fields()
    crops = build.crop_frames(gdf, zonal.clips(default_dir()))
    klass = crops.rotation.set_index("field_id")["field_class"]
    chosen = ["primary-001"] + [klass[klass == c].index[0] for c in ("rotation", "continuous_corn", "pasture_hay", "mixed")]
    chosen += [f for f in gdf[gdf["county"] == "Boone"]["field_id"] if klass[f] == "rotation"][:1]
    projected = gdf.to_crs(zonal.RASTER_CRS).set_index("field_id")
    for field_id in chosen:
        row = projected.loc[field_id]
        for (county, year), clip in zonal.clips(default_dir()).items():
            if county == row["county"]:
                assert dict(zonal.field_counts(clip.path, row.geometry)) == centre_counts(clip.path, row.geometry), (field_id, year)
    primary = crops.rotation.set_index("field_id").loc["primary-001"]
    assert primary["sequence"] == "S C S C S C S C S C S" and primary["field_class"] == "rotation"


@pytest.mark.skipif(not CLIPS_PRESENT, reason="the CDL clips are not on this machine (DE only)")
def test_real_clips_give_the_expected_classes_for_the_decided_fields():
    crops = build.crop_frames(load_fields(), zonal.clips(default_dir()))
    klass = crops.rotation.set_index("field_id")["field_class"]
    assert (klass.loc[["test-039", "test-040", "test-042", "test-043", "test-044"]] == "continuous_corn").all()
    assert (klass == "rotation").sum() == 27


def test_a_field_whose_county_has_no_clips_fails_naming_the_field(monkeypatch):
    monkeypatch.setattr(zonal, "class_names", lambda path: {1: "Corn"})
    gdf = gpd.read_file(FIELDS_PATH)
    only_boone = fake_clips(counties=("Boone",))
    story = gdf[gdf["county"] == "Story"].head(1)
    with pytest.raises(ValueError, match=f"{story['field_id'].iloc[0]}: no CDL clips for Story"):
        build.crop_frames(story, only_boone, lambda p, g: {1: 100})


def test_a_polygon_with_no_pixel_centre_fails_naming_field_and_year(monkeypatch):
    monkeypatch.setattr(zonal, "class_names", lambda path: {1: "Corn"})
    gdf = gpd.read_file(FIELDS_PATH).head(1)
    with pytest.raises(ValueError, match=r"primary-001 2015: the polygon holds no pixel centre"):
        build.crop_frames(gdf, fake_clips(), lambda p, g: {})


def test_a_code_missing_from_the_class_table_or_with_an_empty_name_gets_a_placeholder(monkeypatch):
    monkeypatch.setattr(zonal, "class_names", lambda path: {1: ""})
    gdf = gpd.read_file(FIELDS_PATH).head(1)
    crops = build.crop_frames(gdf, fake_clips(), lambda p, g: {1: 60, 99: 40})
    assert set(crops.shares["cdl_class_name"]) == {"unnamed class 1", "unnamed class 99"}
    CROP_CLASS_SHARES.validate(crops.shares)


def test_a_short_or_gappy_year_window_is_refused_not_judged_on_fewer_transitions():
    labels = {y: rules.label_year({1: 100}) for y in range(2015, 2024)}  # 9 years
    with pytest.raises(ValueError, match="11 years"):
        rules.classify_field(labels)
    gappy = {y: rules.label_year({1: 100}) for y in (*range(2015, 2020), *range(2021, 2027))}  # a hole at 2020
    with pytest.raises(ValueError, match="consecutive"):
        rules.classify_field(gappy)


def test_a_low_confidence_year_names_no_crop():
    label = rules.label_year({1: 70, 0: 30})
    assert label.status == "low_confidence" and label.group == "low_confidence" and label.token == "L"
    assert rules.label_year({0: 100}).group == "low_confidence"  # all no-data is not a non-crop year


def test_the_phase_0_comparison_skips_notes_it_does_not_know():
    from transform.crop_history import run

    fields = pd.DataFrame({"field_id": ["a", "b"], "domain_note": ["in-domain: maize-soybean rotation", "something new"]})
    rotation = pd.DataFrame({"field_id": ["a", "b"], "field_class": ["rotation", "rotation"]})
    crops = build.CropFrames(pd.DataFrame(), pd.DataFrame({"status": ["ok"]}), rotation, {})
    lines = run.summary(fields, crops)
    assert "fields whose class differs from the Phase 0 label: 0 of 1" in lines
    assert any("does not know: b" in line for line in lines)


def test_consistency_check_reports_tables_that_disagree():
    from tests.conftest import FakeClient
    from transform.crop_history import run

    assert run.consistency_problems(FakeClient([("NOT IN", [(0,)]), ("uniqExact", [(1,)])])) == []
    client = FakeClient([("NOT IN", [(2,)]), ("uniqExact", [(2,)])])
    problems = run.consistency_problems(client)
    assert any("crop_history: 2 rows for unknown fields" in p for p in problems)
    assert any("2 rule versions" in p for p in problems)


def test_the_runner_reports_a_missing_clip_folder_cleanly(tmp_path, capsys):
    from transform.crop_history import run

    assert run.main(["--dir", str(tmp_path), "--out", str(tmp_path / "out")]) == 1
    assert "crop history:" in capsys.readouterr().out
