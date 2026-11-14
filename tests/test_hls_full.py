from datetime import UTC, datetime

import geopandas as gpd
import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin
from rasterio.warp import transform_bounds

from ingest import hls
from ingest.items import run_items
from ingest.subset import field_bboxes, union_bbox
from tests.test_s3_store import FakeS3
from transform.field_schema import FIELDS_PATH

FIELDS = gpd.read_file(FIELDS_PATH)
WINDOWS = field_bboxes(FIELDS, hls.BUFFER_M)
BIG = tuple(transform_bounds("EPSG:4326", "EPSG:32615", *union_bbox(FIELDS, 5000)))  # covers every field
SMALL = (BIG[0], BIG[1], BIG[0] + 1000, BIG[1] + 1000)  # a tile that covers almost nothing


def _scene(sensor, day, tile="T15TVG", month=6, sensing="170000"):
    when = datetime(2023, month, day, 17, 0, tzinfo=UTC)
    gid = f"HLS.{sensor.upper()}.{tile}.2023{when.timetuple().tm_yday:03d}T{sensing}.v2.0"
    return hls.Scene(sensor, gid, tile, when, 5.0, {b: f"https://example.test/{gid}.{b}.tif" for b in hls.BANDS[sensor]})


def _searcher(scenes):
    return lambda sensor, bbox, year: [s for s in scenes if s.sensor == sensor]


def _bounds(scene, resolve):
    return BIG if scene.tile == "T15TVG" else SMALL


def _cutter(calls=None, fill=False, count_override=None, no_data_fields=()):
    """`fill`: reflectance all fill but Fmask 0 (a suspicious file). `no_data_fields`: field ids whose
    window the granule does not cover, so the source returns fill and Fmask 255."""
    def cut(scene, jobs, resolve):
        if calls is not None:
            calls.append(scene.granule)
        n = count_override or len(hls.BANDS[scene.sensor])
        for bbox, dest in jobs:
            left, bottom, right, top = transform_bounds("EPSG:4326", "EPSG:32615", *bbox)
            left, top = left - 60, top + 60
            cols, rows = int((right - left) / 30) + 4, int((top - bottom) / 30) + 4
            empty = dest.parent.parent.name in no_data_fields
            data = np.full((n, rows, cols), -9999 if fill or empty else 500, "int16")
            data[-1] = 255 if empty else 0
            dest.parent.mkdir(parents=True, exist_ok=True)
            with rasterio.open(dest, "w", driver="GTiff", height=rows, width=cols, count=n, dtype="int16",
                               crs="EPSG:32615", transform=from_origin(left, top, 30, 30)) as out:
                out.write(data)
        return len(jobs)
    return cut


@pytest.fixture(autouse=True)
def _no_login(monkeypatch):
    from contextlib import contextmanager

    @contextmanager
    def stub():
        yield lambda href: href

    monkeypatch.setattr(hls, "earthdata_session", stub)


def _plan(tmp_path, scenes, cutter=None):
    return hls.plan_full(tmp_path, (2023,), _searcher(scenes), cutter or _cutter(), _bounds)


def test_the_tile_covering_most_fields_is_used_and_a_field_it_misses_falls_back():
    one = hls.assign_tiles(WINDOWS, {"T15TVG": BIG, "T15TUG": SMALL})
    assert set(one.values()) == {"T15TVG"}
    a = (-93.60, 42.00, -93.59, 42.01)  # three small windows, far enough apart to be unambiguous
    b = (-93.50, 42.00, -93.49, 42.01)
    c = (-93.20, 42.00, -93.19, 42.01)
    windows = {"a": a, "b": b, "c": c}

    def around(*frames):
        pieces = [transform_bounds("EPSG:4326", "EPSG:32615", *f) for f in frames]
        return (min(p[0] for p in pieces) - 100, min(p[1] for p in pieces) - 100,
                max(p[2] for p in pieces) + 100, max(p[3] for p in pieces) + 100)

    out = hls.assign_tiles(windows, {"T15TUG": around(c), "T15TVG": around(a, b)})
    assert out == {"a": "T15TVG", "b": "T15TVG", "c": "T15TUG"}  # most fields first, c falls back
    with pytest.raises(RuntimeError, match="no single HLS tile"):
        hls.assign_tiles(windows, {"T15TVG": around(a, b)})


def test_each_scene_gives_one_stack_per_field_with_the_agreed_name_and_key(tmp_path):
    items = _plan(tmp_path, [_scene("l30", 15), _scene("s30", 16)])
    assert len(items) == 2 * 45 and all(i.checks.ok for i in items), [i.checks.problems for i in items if not i.checks.ok][:2]
    keys = {(i.source, i.key_name) for i in items}
    assert ("hls/l30", "primary-001/20230615/T170000_stack_b04_b05_b06_fmask.tif") in keys
    assert ("hls/s30", "test-044/20230616/T170000_stack_b04_b8a_b11_fmask.tif") in keys


def test_two_scenes_of_one_tile_on_one_day_are_both_kept(tmp_path):
    early, late = _scene("s30", 10, sensing="165849"), _scene("s30", 10, sensing="171711")
    items = _plan(tmp_path, [early, late])
    names = {i.key_name for i in items if i.key_name.startswith("primary-001/")}
    assert names == {"primary-001/20230610/T165849_stack_b04_b8a_b11_fmask.tif",
                     "primary-001/20230610/T171711_stack_b04_b8a_b11_fmask.tif"}
    assert len(items) == 2 * 45 and all(i.checks.ok for i in items)
    client = FakeS3()
    assert run_items(items, client, "bkt", execute=True) == 0
    assert sum(k.endswith(".tif") for k in client.objects) == 90  # nothing overwritten or dropped


def test_manifest_gives_band_order_window_and_the_fmask_storage_note(tmp_path):
    item = next(i for i in _plan(tmp_path, [_scene("s30", 16)]) if i.key_name.startswith("primary-001/"))
    sub = item.manifest.subset
    assert sub["bands"] == ["B04", "B8A", "B11", "Fmask"] and sub["field_id"] == "primary-001" and sub["kind"] == "window-stack"
    assert "Fmask is uint8 in the source" in item.manifest.notes and "5 water" in item.manifest.notes
    assert item.manifest.evidence_type == "observed"


def test_a_stack_already_on_disk_is_not_cut_again(tmp_path):
    calls = []
    scenes = [_scene("l30", 15)]
    _plan(tmp_path, scenes, _cutter(calls))
    _plan(tmp_path, scenes, _cutter(calls))
    assert calls == ["HLS.L30.T15TVG.2023166T170000.v2.0"]


def test_a_failed_scene_is_reported_and_the_others_are_kept(tmp_path):
    good = _cutter()

    def flaky(scene, jobs, resolve):
        if scene.acquired.day == 16:
            raise OSError("connection reset")
        return good(scene, jobs, resolve)

    with pytest.raises(RuntimeError, match="1 scenes failed"):
        _plan(tmp_path, [_scene("l30", 15), _scene("l30", 16)], flaky)
    assert (tmp_path / "stacks/l30/primary-001/20230615").exists()


def test_stacks_with_the_wrong_band_count_or_only_fill_fail_their_check(tmp_path):
    scenes = [_scene("l30", 15)]
    wrong = _plan(tmp_path / "a", scenes, _cutter(count_override=3))
    assert any("expected 4 of int16" in p for i in wrong for p in i.checks.problems)
    empty = _plan(tmp_path / "b", scenes, _cutter(fill=True))
    assert any("every reflectance pixel is fill" in p for i in empty for p in i.checks.problems)


def test_a_winter_scene_fails_its_check(tmp_path):
    winter = _scene("l30", 10, month=1)
    items = _plan(tmp_path, [winter])
    assert any("outside April to October" in p for i in items for p in i.checks.problems)


def test_window_for_returns_a_window_that_covers_the_requested_box():
    frame = WINDOWS["primary-001"]
    left, bottom, right, top = transform_bounds("EPSG:4326", "EPSG:32615", *frame)

    class Src:
        crs = rasterio.crs.CRS.from_epsg(32615)
        res = (30.0, 30.0)
        transform = from_origin(left - 5000, top + 5000, 30, 30)

    window, transform = hls.window_for(Src, frame)
    w_left, w_top = transform.c, transform.f
    w_right, w_bottom = w_left + window.width * 30, w_top - window.height * 30
    assert w_left <= left and w_bottom <= bottom and w_right >= right and w_top >= top
    assert window.width * 30 - (right - left) < 90  # no more than a pixel or two of slack


def test_the_stacks_upload_in_parallel_with_the_ds1_key_layout(tmp_path):
    items = _plan(tmp_path / "data", [_scene("l30", 15), _scene("l30", 16)])
    client = FakeS3()
    assert run_items(items, client, "bkt", execute=True) == 0
    day = items[0].manifest.retrieval_date
    assert f"raw/hls/l30/v2.0/{day}/primary-001/20230615/T170000_stack_b04_b05_b06_fmask.tif" in client.objects
    assert sum(k.endswith(".tif") for k in client.objects) == 90


EMPTY = ("test-001", "test-002", "test-003")


def test_windows_the_granule_does_not_cover_are_listed_and_not_uploaded(tmp_path):
    items = _plan(tmp_path, [_scene("l30", 15), _scene("s30", 16)], _cutter(no_data_fields=EMPTY))
    tifs = [i for i in items if i.key_name.endswith(".tif")]
    assert len(tifs) == 2 * 42 and all(i.checks.ok for i in items)
    assert not any(i.key_name.split("/")[0] in EMPTY for i in tifs)
    lines = (tmp_path / hls.NO_DATA_FILE).read_text().splitlines()
    assert lines[0] == "sensor,field_id,date,granule,tile" and len(lines) == 1 + 2 * 3
    assert "l30,test-001,2023-06-15,HLS.L30.T15TVG.2023166T170000.v2.0,T15TVG" in lines


def test_the_no_data_list_is_uploaded_with_its_own_manifest(tmp_path):
    items = _plan(tmp_path, [_scene("l30", 15)], _cutter(no_data_fields=EMPTY))
    listing = next(i for i in items if i.key_name == hls.NO_DATA_FILE)
    assert listing.source == "hls/no-data" and listing.manifest.subset == {
        "kind": "no-data-list", "windows": 3, "fields": 3}
    assert "unknown" in listing.manifest.notes
    client = FakeS3()
    assert run_items(items, client, "bkt", execute=True) == 0
    day = listing.manifest.retrieval_date
    assert f"raw/hls/no-data/v2.0/{day}/skipped_no_data.csv" in client.objects
    assert sum(k.endswith(".tif") for k in client.objects) == 42


def test_no_list_is_made_when_every_window_has_data(tmp_path):
    items = _plan(tmp_path, [_scene("l30", 15)])
    assert not any(i.key_name == hls.NO_DATA_FILE for i in items)
    assert not (tmp_path / hls.NO_DATA_FILE).exists()


def test_stack_is_no_data_needs_fill_and_fmask_255(tmp_path):
    def make(name, fill, fmask):
        path = tmp_path / name
        with rasterio.open(path, "w", driver="GTiff", height=4, width=4, count=4, dtype="int16",
                           crs="EPSG:32615", transform=from_origin(0, 4, 1, 1)) as out:
            data = np.full((4, 4, 4), fill, "int16")
            data[-1] = fmask
            out.write(data)
        return path

    assert hls.stack_is_no_data(make("empty.tif", -9999, 255))
    assert not hls.stack_is_no_data(make("fill_other_fmask.tif", -9999, 0))  # odd: still fails its check
    assert not hls.stack_is_no_data(make("data.tif", 500, 255))
    assert not hls.stack_is_no_data(tmp_path / "missing.tif")
