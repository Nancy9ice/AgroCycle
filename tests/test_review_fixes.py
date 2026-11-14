"""Tests for the problems found by the code review of the Phase 1 branch."""

import io
import json
import os
import urllib.error
from datetime import UTC, date, datetime

import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin

from ingest import hls, items, power
from ingest.checks import CheckResult
from ingest.items import Item, run_items
from ingest.manifest import build_manifest
from ingest.s3_store import (
    AlreadyExistsError,
    ChecksumMismatchError,
    manifest_key,
    raw_key,
    upload_raw,
)
from tests.test_s3_store import FIELDS, FakeS3


@pytest.fixture
def data_file(tmp_path):
    path = tmp_path / "data.csv"
    path.write_bytes(b"a,b\n1,2\n")
    return path


# --- an interrupted upload can be finished, never left as a data file without a manifest ---------
def _key():
    return raw_key("power", "v1", "2026-11-14", "data.csv")


def test_a_data_file_left_without_its_manifest_is_completed_on_the_next_run(data_file):
    client = FakeS3()
    manifest = build_manifest(data_file, **FIELDS)
    client.objects[_key()] = data_file.read_bytes()  # the run stopped between the two writes
    assert upload_raw(client, "bkt", data_file, manifest, source="power") == _key()
    assert manifest_key(_key()) in client.objects
    with pytest.raises(AlreadyExistsError):  # and now it is complete, so a third run skips it
        upload_raw(client, "bkt", data_file, manifest, source="power")


def test_a_half_written_file_with_the_wrong_content_is_not_blessed_with_a_manifest(data_file):
    client = FakeS3()
    client.objects[_key()] = b"something else"
    with pytest.raises(ChecksumMismatchError):
        upload_raw(client, "bkt", data_file, build_manifest(data_file, **FIELDS), source="power")
    assert manifest_key(_key()) not in client.objects


def test_a_manifest_without_its_data_file_is_reported_not_overwritten(data_file):
    client = FakeS3()
    client.objects[manifest_key(_key())] = b"{}"
    with pytest.raises(RuntimeError, match="needs a manual look"):
        upload_raw(client, "bkt", data_file, build_manifest(data_file, **FIELDS), source="power")


def test_a_dry_run_of_a_half_finished_upload_writes_nothing(data_file):
    client = FakeS3()
    client.objects[_key()] = data_file.read_bytes()
    upload_raw(client, "bkt", data_file, build_manifest(data_file, **FIELDS), source="power", dry_run=True)
    assert manifest_key(_key()) not in client.objects


# --- a resumed run still shows progress ------------------------------------------------------------
def test_progress_is_printed_even_when_every_item_is_skipped(data_file, monkeypatch, capsys):
    client = FakeS3()
    item = Item(data_file, build_manifest(data_file, **FIELDS), CheckResult(), "power")
    run_items([item], client, "bkt", execute=True)
    monkeypatch.setattr(items, "PROGRESS_EVERY", 1)
    run_items([item], client, "bkt", execute=True)
    assert "1 of 1 handled" in capsys.readouterr().out


# --- POWER: a 4xx is not retried, an error payload is not cached -------------------------------------
def _http_error(code):
    return urllib.error.HTTPError("https://power.test", code, "x", {}, io.BytesIO(b""))


def test_a_rejected_request_is_not_retried_but_a_server_error_is(monkeypatch):
    calls = []

    def urlopen(url, timeout):
        calls.append(url)
        raise _http_error(422 if len(calls) == 1 else 503)

    monkeypatch.setattr(power.urllib.request, "urlopen", urlopen)
    monkeypatch.setattr(power.time, "sleep", lambda s: None)
    with pytest.raises(RuntimeError, match="after 1 tries"):
        power.fetch("https://power.test/a")
    assert len(calls) == 1
    calls.clear()
    monkeypatch.setattr(power.urllib.request, "urlopen", lambda url, timeout: calls.append(url) or (_ for _ in ()).throw(_http_error(503)))
    with pytest.raises(RuntimeError, match="after 3 tries"):
        power.fetch("https://power.test/b")
    assert len(calls) == 3


def test_an_error_payload_is_reported_and_never_kept_as_the_cached_pull(tmp_path, monkeypatch):
    start, end = date(2003, 1, 1), date(2003, 1, 3)
    monkeypatch.setattr(power, "FIRST_PULL", (start, end))
    dates = power.expected_dates(start, end)
    good = json.dumps({
        "geometry": {"coordinates": [-93.783, 42.017, 310.2]},
        "properties": {"parameter": {v: dict.fromkeys(dates, 1.0) for v in power.VARIABLES}},
        "header": {"fill_value": -999.0, "time_standard": "LST", "sources": ["MERRA2"], "api": {"version": "v2"}},
    }).encode()
    (bad,) = power.plan_first_pull(tmp_path, lambda url: b'{"messages": ["rate limited"]}')
    assert not bad.checks.ok and list(tmp_path.glob("*.json")) == []  # nothing cached
    (ok,) = power.plan_first_pull(tmp_path, lambda url: good)  # the next run asks again and succeeds
    assert ok.checks.ok and len(list(tmp_path.glob("*.json"))) == 1


# --- HLS: bands are closed on failure, windows outside the tile are refused, one run date --------------
class FakeBand:
    def __init__(self, fail=False, origin=(400000.0, 4650000.0)):
        if fail:
            raise OSError("band could not be opened")
        self.closed = False
        self.crs = rasterio.crs.CRS.from_epsg(32615)
        self.res = (30.0, 30.0)
        self.transform = from_origin(*origin, 30, 30)
        self.shape, (self.height, self.width) = (3660, 3660), (3660, 3660)

    def read(self, band, window=None):
        return np.zeros((window.height, window.width), "int16")

    def close(self):
        self.closed = True


def _scene():
    when = datetime(2023, 6, 15, 17, 0, tzinfo=UTC)
    return hls.Scene("l30", "HLS.L30.T15TVG.2023166T170000.v2.0", "T15TVG", when, 5.0,
                     {b: f"https://x.test/{b}" for b in hls.BANDS["l30"]})


def test_bands_already_opened_are_closed_when_a_later_band_fails(monkeypatch):
    opened = []

    def fake_open(url):
        if url.endswith("B06"):
            return FakeBand(fail=True)
        band = FakeBand()
        opened.append(band)
        return band

    monkeypatch.setattr(hls.rasterio, "open", fake_open)
    with pytest.raises(OSError, match="could not be opened"):
        hls.cut_scene(_scene(), [((-93.5, 42.0, -93.49, 42.01), "unused")], lambda href: href)
    assert len(opened) == 2 and all(band.closed for band in opened)


def test_a_window_outside_the_tile_is_refused_instead_of_cut(monkeypatch, tmp_path):
    monkeypatch.setattr(hls.rasterio, "open", lambda url: FakeBand(origin=(100000.0, 4000000.0)))
    with pytest.raises(RuntimeError, match="falls outside the tile"):
        hls.cut_scene(_scene(), [((-93.5, 42.0, -93.49, 42.01), tmp_path / "x.tif")], lambda href: href)


def test_one_clip_error_does_not_hide_the_others(tmp_path, monkeypatch):
    from contextlib import contextmanager

    @contextmanager
    def stub():
        yield lambda href: href

    monkeypatch.setattr(hls, "earthdata_session", stub)
    scenes = [_scene()]

    def odd_error(href, bbox, dest, resolve):
        raise KeyError("unexpected")

    with pytest.raises(RuntimeError, match=r"4 of 4 clips failed"):
        hls.pull(tmp_path, "primary-001", (-93.5, 42.0, -93.49, 42.01), 2023, lambda sensor, b, y: scenes if sensor == "l30" else [], odd_error)


def test_the_whole_full_run_shares_one_retrieval_date(tmp_path, monkeypatch):
    from contextlib import contextmanager

    from tests.test_hls_full import SMALL, _bounds, _cutter, _searcher  # noqa: F401
    from tests.test_hls_full import _scene as scene_for

    @contextmanager
    def stub():
        yield lambda href: href

    monkeypatch.setattr(hls, "earthdata_session", stub)
    scenes = [scene_for("l30", 15), scene_for("l30", 16)]
    hls.plan_full(tmp_path, (2023,), _searcher(scenes), _cutter(), _bounds)
    first = next(tmp_path.rglob("T170000_stack_*.tif"))
    two_days_ago = datetime.now().timestamp() - 2 * 86400
    os.utime(first, (two_days_ago, two_days_ago))  # as if one stack was cut before midnight
    again = hls.plan_full(tmp_path, (2023,), _searcher(scenes), _cutter(), _bounds)
    assert len({i.manifest.retrieval_date for i in again}) == 1
