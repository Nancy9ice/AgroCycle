from datetime import UTC, date, datetime

import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin
from rasterio.warp import transform_bounds

from ingest import hls
from ingest.items import run_items
from tests.test_s3_store import FakeS3


def _scene(sensor, day, granule=None, tile="T15TVG"):
    when = datetime(2023, 6, day, 17, 0, tzinfo=UTC)
    gid = granule or f"HLS.{sensor.upper()}.{tile}.2023{when.timetuple().tm_yday:03d}T170000.v2.0"
    return hls.Scene(sensor, gid, tile, when, 10.0, {b: f"https://example.test/{gid}.{b}.tif" for b in hls.BANDS[sensor]})


def _searcher(scenes):
    return lambda sensor, bbox, year: [s for s in scenes if s.sensor == sensor]


def _clipper(calls=None, fill_all=False, crs="EPSG:32615", dtype_override=None):
    """Writes a small raster that covers the requested window, like a real clip would."""
    def clip(href, bbox, dest, resolve):
        if calls is not None:
            calls.append(href)
        left, bottom, right, top = transform_bounds("EPSG:4326", "EPSG:32615", *bbox)
        left, top = left - 60, top + 60  # a little more than asked, as a real window rounds outward
        cols, rows = int((right - left) / 30) + 4, int((top - bottom) / 30) + 4
        band = href.rsplit(".", 2)[-2]
        dtype = dtype_override or ("uint8" if band == "Fmask" else "int16")
        fill = 255 if dtype == "uint8" else -9999
        value = 0 if band == "Fmask" else 500  # Fmask 0 means no flag is set
        data = np.full((rows, cols), fill if fill_all else value, dtype)
        dest.parent.mkdir(parents=True, exist_ok=True)
        with rasterio.open(dest, "w", driver="GTiff", height=rows, width=cols, count=1, dtype=dtype,
                           crs=crs, nodata=fill, transform=from_origin(left, top, 30, 30)) as out:
            out.write(data, 1)
        return {"cols": cols, "rows": rows}
    return clip


@pytest.fixture(autouse=True)
def _no_login(monkeypatch):
    """The fake clipper never needs a login, so the real login is replaced by a stub."""
    from contextlib import contextmanager

    @contextmanager
    def stub():
        yield lambda href: href

    monkeypatch.setattr(hls, "earthdata_session", stub)


def test_each_scene_gets_the_four_bands_of_its_sensor_under_the_ds1_layout(tmp_path):
    scenes = [_scene("l30", 15), _scene("s30", 16)]
    items = hls.plan_field("primary-001", 2023, tmp_path, _searcher(scenes), _clipper())
    keys = {(i.source, i.key_name) for i in items}
    assert len(items) == 8 and all(i.checks.ok for i in items), [i.checks.problems for i in items]
    assert ("hls/l30", "primary-001/20230615/b05.tif") in keys
    assert ("hls/s30", "primary-001/20230616/b8a.tif") in keys and ("hls/s30", "primary-001/20230616/fmask.tif") in keys
    assert not any(k[1].endswith("b08.tif") for k in keys)  # the broad NIR band is never taken


def test_manifest_records_granule_window_and_that_values_are_unmasked(tmp_path):
    (item, *_) = hls.plan_field("primary-001", 2023, tmp_path, _searcher([_scene("l30", 15)]), _clipper())
    sub = item.manifest.subset
    assert sub["field_id"] == "primary-001" and sub["granule"].startswith("HLS.L30.T15TVG") and sub["tile"] == "T15TVG"
    assert item.manifest.evidence_type == "observed" and "unmasked and unscaled" in item.manifest.notes
    fmask = next(i for i in hls.plan_field("primary-001", 2023, tmp_path, _searcher([_scene("l30", 15)]), _clipper())
                 if i.key_name.endswith("fmask.tif"))
    assert "5 water" in fmask.manifest.notes  # NASA's verified bit layout travels with the Fmask files


def test_files_already_clipped_are_not_read_again(tmp_path):
    calls = []
    scenes = [_scene("l30", 15)]
    hls.plan_field("primary-001", 2023, tmp_path, _searcher(scenes), _clipper(calls))
    first = len(calls)
    hls.plan_field("primary-001", 2023, tmp_path, _searcher(scenes), _clipper(calls))
    assert first == 4 and len(calls) == first


def test_two_granules_on_one_date_are_refused_not_silently_merged(tmp_path):
    scenes = [_scene("l30", 15), _scene("l30", 15, granule="HLS.L30.T15TVG.2023166T171500.v2.0")]
    with pytest.raises(RuntimeError, match="two granules on one date"):
        hls.plan_field("primary-001", 2023, tmp_path, _searcher(scenes), _clipper())


def test_failed_clips_are_all_reported_and_the_rest_are_kept(tmp_path):
    good = _clipper()

    def flaky(href, bbox, dest, resolve):
        if href.endswith(".B05.tif"):
            raise OSError("connection reset")
        return good(href, bbox, dest, resolve)

    with pytest.raises(RuntimeError, match=r"1 of 4 clips failed"):
        hls.plan_field("primary-001", 2023, tmp_path, _searcher([_scene("l30", 15)]), flaky)
    assert (tmp_path / "l30/primary-001/20230615/b04.tif").exists()  # kept, so a rerun only retries B05


def test_wrong_crs_wrong_dtype_and_empty_clips_fail_their_checks(tmp_path):
    scenes = [_scene("l30", 15)]
    bad_crs = hls.plan_field("primary-001", 2023, tmp_path / "a", _searcher(scenes), _clipper(crs="EPSG:32616"))
    assert any("CRS" in p for i in bad_crs for p in i.checks.problems)
    empty = hls.plan_field("primary-001", 2023, tmp_path / "b", _searcher(scenes), _clipper(fill_all=True))
    assert any("every pixel is fill" in p for i in empty for p in i.checks.problems)
    wrong = hls.plan_field("primary-001", 2023, tmp_path / "c", _searcher(scenes), _clipper(dtype_override="float32"))
    assert any("dtype float32" in p for i in wrong for p in i.checks.problems)


def test_a_scene_outside_april_to_october_fails_its_check(tmp_path):
    winter = hls.Scene("l30", "HLS.L30.T15TVG.2023010T170000.v2.0", "T15TVG",
                       datetime(2023, 1, 10, 17, 0, tzinfo=UTC), 5.0,
                       {b: f"https://example.test/w.{b}.tif" for b in hls.BANDS["l30"]})
    items = hls.plan_field("primary-001", 2023, tmp_path, _searcher([winter]), _clipper())
    assert any("outside April to October" in p for i in items for p in i.checks.problems)


def test_the_items_upload_with_checksums_and_the_ds1_key_layout(tmp_path):
    items = hls.plan_field("primary-001", 2023, tmp_path / "data", _searcher([_scene("l30", 15)]), _clipper())
    client = FakeS3()
    assert run_items(items, client, "bkt", execute=True) == 0
    day = items[0].manifest.retrieval_date
    assert f"raw/hls/l30/v2.0/{day}/primary-001/20230615/b04.tif" in client.objects


def test_season_dates_and_band_choices_match_ds1s_sheet():
    assert hls.BANDS["l30"] == ("B04", "B05", "B06", "Fmask") and hls.BANDS["s30"] == ("B04", "B8A", "B11", "Fmask")
    assert hls.BUFFER_M == 500 and hls.TILE_CRS == "EPSG:32615" and date(2023, 4, 1) < date(2023, 10, 31)
