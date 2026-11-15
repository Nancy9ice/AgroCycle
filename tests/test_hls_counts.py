"""Counts per window, the local and S3 sources, the schema, and (when the pull is here) the real 16,560 windows."""

import csv
import io
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
import pandera.errors
import pytest
import rasterio
import shapely
from rasterio.transform import from_origin
from shapely.geometry import box

from common.schemas import HLS_VALID_PIXELS
from transform.hls import counts, mask, sources

SCHEMA_ERRORS = (pandera.errors.SchemaError, pandera.errors.SchemaErrors)
TF = from_origin(500000, 4650000, 30, 30)
POLYGON = box(500030, 4649880, 500150, 4649970)  # columns 1-4, rows 1-3: 12 pixels
HLS_DIR = sources.default_pull_dir()


def array(fmask=0, reflectance=500, fill_window=False):
    data = np.full((4, 6, 6), reflectance, dtype=np.int16)
    data[-1] = fmask
    if fill_window:
        data[:-1] = mask.REFLECTANCE_FILL
        data[-1] = mask.FMASK_FILL
    return data


def write_stack(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(path, "w", driver="GTiff", height=6, width=6, count=4, dtype="int16",
                       crs=mask.TILE_CRS, transform=TF) as out:
        out.write(data)


def test_a_clear_window_has_every_polygon_pixel_valid():
    result = counts.count_stack(mask.Stack(array(), TF, mask.TILE_CRS), POLYGON)
    assert (result.total, result.fill, result.flagged, result.valid, result.no_data) == (12, 0, 0, 12, False)


def test_cloud_fill_and_valid_pixels_are_counted_apart():
    data = array()
    data[-1, 1, 1:3] = 2  # two cloud pixels inside the polygon
    data[-1, 3, 4] = 255  # one fill pixel inside
    data[-1, 0, 0] = 2  # cloud outside the polygon: not counted
    result = counts.count_stack(mask.Stack(data, TF, mask.TILE_CRS), POLYGON)
    assert (result.total, result.fill, result.flagged, result.valid) == (12, 1, 2, 9)


def test_a_window_with_no_data_is_no_observation_with_zero_valid_pixels():
    result = counts.count_stack(mask.Stack(array(fill_window=True), TF, mask.TILE_CRS), POLYGON)
    assert (result.total, result.fill, result.valid, result.no_data) == (12, 12, 0, True)


def test_a_window_fully_cloudy_inside_the_field_is_observed_not_no_data():
    data = array()
    data[-1, 1:4, 1:5] = 2  # the whole polygon is cloud; the window still holds data elsewhere
    result = counts.count_stack(mask.Stack(data, TF, mask.TILE_CRS), POLYGON)
    assert result.valid == 0 and result.flagged == 12 and not result.no_data


def build_tree(tmp_path):
    """A tiny local pull: one clear L30 scene, one S30 scene with cloud, one no-data scene, and a stray file."""
    base = tmp_path / "stacks"
    write_stack(base / "l30" / "f1" / "20230405" / "T165930_stack_b04_b05_b06_fmask.tif", array())
    cloudy = array()
    cloudy[-1, 1, 1] = 2
    write_stack(base / "s30" / "f1" / "20230406" / "T170001_stack_b04_b8a_b11_fmask.tif", cloudy)
    write_stack(base / "l30" / "f1" / "20230414" / "T165311_stack_b04_b05_b06_fmask.tif", array(fill_window=True))
    (base / "l30" / "f1" / "20230405" / "notes.txt").write_text("not a stack")
    return tmp_path


def test_the_local_source_finds_the_stacks_and_ignores_other_files(tmp_path):
    windows = sources.LocalSource(build_tree(tmp_path)).windows()
    assert [(w.sensor, w.acquired, w.sensing_time) for w in windows] == [
        ("l30", date(2023, 4, 5), "T165930"), ("l30", date(2023, 4, 14), "T165311"), ("s30", date(2023, 4, 6), "T170001"),
    ]
    assert windows[0].s3_key == "raw/hls/l30/v2.0/2026-11-14/f1/20230405/T165930_stack_b04_b05_b06_fmask.tif"


def test_count_windows_gives_one_row_per_window_and_passes_the_schema(tmp_path):
    source = sources.LocalSource(build_tree(tmp_path))
    frame = counts.count_windows(source, {"f1": POLYGON})
    # by date: 5 April clear, 6 April cloudy (one cloud pixel in the polygon), 14 April no data
    assert len(frame) == 3 and frame["status"].tolist() == ["observed", "observed", "no_data"]
    assert frame["valid_pixels"].tolist() == [12, 11, 0] and frame["total_pixels"].unique().tolist() == [12]
    HLS_VALID_PIXELS.validate(frame)


class FakeS3:
    """Just enough of the S3 client for the source: a listing and object reads from a dict."""

    def __init__(self, objects: dict[str, bytes]):
        self.objects = objects

    def get_paginator(self, name):
        outer = self

        class Pages:
            def paginate(self, Bucket, Prefix):
                yield {"Contents": [{"Key": k} for k in sorted(outer.objects) if k.startswith(Prefix)]}

        return Pages()

    def get_object(self, Bucket, Key):
        return {"Body": io.BytesIO(self.objects[Key])}


def tif_bytes(data) -> bytes:
    with rasterio.MemoryFile() as memory:
        with memory.open(driver="GTiff", height=6, width=6, count=4, dtype="int16", crs=mask.TILE_CRS, transform=TF) as out:
            out.write(data)
        return memory.read()


def test_the_s3_source_lists_stacks_reads_them_and_adds_the_windows_that_only_the_list_knows():
    key = "raw/hls/l30/v2.0/2026-11-14/f1/20230405/T165930_stack_b04_b05_b06_fmask.tif"
    out = io.StringIO()
    writer = csv.DictWriter(out, fieldnames=["sensor", "field_id", "date", "granule", "tile"], lineterminator="\n")
    writer.writeheader()
    writer.writerow({"sensor": "l30", "field_id": "f1", "date": "2023-04-14",
                     "granule": "HLS.L30.T15TVG.2023104T165311.v2.0", "tile": "T15TVG"})
    client = FakeS3({
        key: tif_bytes(array()), key + ".manifest.json": b"{}",
        "raw/hls/l30/v2.0/2026-11-14/f1/20230405/b04.tif": b"first-pull band file, not a stack",
        sources.NO_DATA_KEY: out.getvalue().encode(),
    })
    source = sources.S3Source(client, "bucket")
    assert [w.name for w in source.windows()] == ["T165930_stack_b04_b05_b06_fmask.tif"]
    frame = counts.count_windows(source, {"f1": POLYGON})
    assert frame["status"].tolist() == ["observed", "no_data"]
    listed = frame.iloc[1]
    assert (listed["total_pixels"], listed["fill_pixels"], listed["valid_pixels"]) == (12, 12, 0)
    assert listed["source_s3_key"] == sources.NO_DATA_KEY and listed["sensing_time"] == "T165311"
    HLS_VALID_PIXELS.validate(frame)


def good_frame(tmp_path):
    return counts.count_windows(sources.LocalSource(build_tree(tmp_path)), {"f1": POLYGON})


def test_the_schema_rejects_counts_that_do_not_add_up(tmp_path):
    frame = good_frame(tmp_path)
    with pytest.raises(SCHEMA_ERRORS):
        HLS_VALID_PIXELS.validate(frame.assign(valid_pixels=frame["valid_pixels"] + 1))
    with pytest.raises(SCHEMA_ERRORS):
        HLS_VALID_PIXELS.validate(frame.assign(valid_share=0.5))


def test_the_schema_rejects_a_no_data_window_that_claims_a_valid_pixel(tmp_path):
    frame = good_frame(tmp_path)
    lie = frame.copy()
    lie.loc[lie["status"] == "no_data", ["fill_pixels", "valid_pixels"]] = [11, 1]
    lie["valid_share"] = lie["valid_pixels"] / lie["total_pixels"]
    with pytest.raises(SCHEMA_ERRORS):
        HLS_VALID_PIXELS.validate(lie)


def test_the_schema_rejects_duplicates_bad_sensors_and_bad_times(tmp_path):
    frame = good_frame(tmp_path)
    with pytest.raises(SCHEMA_ERRORS):
        HLS_VALID_PIXELS.validate(pd.concat([frame, frame.head(1)], ignore_index=True))
    with pytest.raises(SCHEMA_ERRORS):
        HLS_VALID_PIXELS.validate(frame.assign(sensor="modis"))
    with pytest.raises(SCHEMA_ERRORS):
        HLS_VALID_PIXELS.validate(frame.assign(sensing_time="165930"))


def test_run_reports_a_missing_pull_cleanly(tmp_path, capsys):
    from transform.hls import run

    assert run.main(["--dir", str(tmp_path), "--out", str(tmp_path / "out")]) == 1
    assert "hls:" in capsys.readouterr().out


def test_run_summary_names_the_windows_with_no_valid_pixel(tmp_path):
    from transform.hls import run

    lines = run.summary(good_frame(tmp_path))
    assert "3 windows (2 observed, 1 no data) for 1 fields" in lines[0]


HAVE_PULL = (HLS_DIR / "stacks").exists()
SKIP = pytest.mark.skipif(not HAVE_PULL, reason="the HLS pull is not on this machine (DE only)")


@pytest.fixture(scope="module")
def real():
    source = sources.LocalSource()
    polygons = counts.field_polygons()
    return source, polygons, counts.count_windows(source, polygons)


@SKIP
def test_all_16560_windows_are_counted_once_and_the_no_data_ones_match_the_phase_1_list(real):
    _, _, frame = real
    assert len(frame) == 16_560 and frame["status"].value_counts().to_dict() == {"observed": 14_598, "no_data": 1_962}
    listed = HLS_DIR / "skipped_no_data.csv"
    if listed.exists():
        rows = list(csv.DictReader(listed.open()))
        wanted = {(r["field_id"], r["sensor"], r["date"], "T" + r["granule"].split(".")[3].split("T")[1]) for r in rows}
        got = {(r.field_id, r.sensor, f"{r.acquired:%Y-%m-%d}", r.sensing_time)
               for r in frame[frame["status"] == "no_data"].itertuples()}
        assert got == wanted


@SKIP
def test_each_fields_polygon_pixel_count_is_the_same_in_every_window(real):
    _, _, frame = real
    per = frame.groupby("field_id")["total_pixels"].agg(["min", "max"])
    assert (per["min"] == per["max"]).all() and len(per) == 45


@SKIP
def test_the_primary_field_and_five_others_match_an_independent_recount_for_every_window(real):
    source, polygons, frame = real
    chosen = ["primary-001", "test-001", "test-010", "test-020", "test-033", "test-039"]
    checked = 0
    for window in (w for w in source.windows() if w.field_id in chosen):
        scene = source.read(window)
        polygon = polygons[window.field_id]
        rows, cols = scene.data.shape[1:]
        ys, xs = np.indices((rows, cols))
        px, py = scene.transform @ (xs + 0.5, ys + 0.5)
        inside = shapely.contains_xy(polygon, px, py)
        fmask = scene.data[-1].astype(int)
        fill = (fmask == 255) | (scene.data[:-1] == -9999).any(axis=0)
        flagged = ~fill & ((fmask & 62) != 0)  # 62 is 0b00111110
        row = frame[(frame.field_id == window.field_id) & (frame.sensor == window.sensor)
                    & (frame.acquired == pd.Timestamp(window.acquired)) & (frame.sensing_time == window.sensing_time)].iloc[0]
        assert (int(inside.sum()), int((fill & inside).sum()), int((flagged & inside).sum()),
                int((~fill & ~flagged & inside).sum())) == (
            row.total_pixels, row.fill_pixels, row.flagged_pixels, row.valid_pixels)
        checked += 1
    assert checked > 1_000
