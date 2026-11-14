import json
from datetime import date

import pytest

from ingest import power

START, END = date(2003, 1, 1), date(2003, 1, 5)


def _body(start=START, end=END, drop=None, header=None, fill_on=None):
    dates = power.expected_dates(start, end)
    parameter = {v: {d: 1.5 for d in dates} for v in power.VARIABLES if v != drop}
    if fill_on:
        parameter[fill_on][dates[0]] = -999.0
    doc = {
        "geometry": {"type": "Point", "coordinates": [-93.783, 42.017, 310.2]},
        "properties": {"parameter": parameter},
        "header": header or {"fill_value": -999.0, "time_standard": "LST", "sources": ["MERRA2"],
                             "api": {"version": "v2.10.3"}},
    }
    return json.dumps(doc).encode()


def test_a_complete_response_passes_and_reports_the_header():
    result, summary = power.inspect(_body(), START, END)
    assert result.ok and summary["api_version"] == "v2.10.3" and summary["days"] == 5
    assert summary["time_standard"] == "LST" and summary["returned_lat"] == 42.017


def test_fill_values_are_counted_but_kept():
    _, summary = power.inspect(_body(fill_on="T2M"), START, END)
    assert summary["fill_counts"]["T2M"] == 1 and summary["fill_counts"]["WS2M"] == 0


def test_missing_variable_wrong_dates_and_bad_header_are_reported():
    assert any("T2M_MAX: missing" in p for p in power.inspect(_body(drop="T2M_MAX"), START, END)[0].problems)
    short = _body(end=date(2003, 1, 3))
    assert any("expected 5" in p for p in power.inspect(short, START, END)[0].problems)
    no_fill = _body(header={"time_standard": "LST"})
    assert any("fill_value" in p for p in power.inspect(no_fill, START, END)[0].problems)
    assert not power.inspect(b"<html>error</html>", START, END)[0].ok


def test_request_url_has_the_sheet_settings():
    url = power.request_url(42.0167, -93.7833, START, END)
    for part in ("community=AG", "format=JSON", "start=20030101", "end=20030105",
                 "latitude=42.0167", "longitude=-93.7833", "T2M_MAX,T2M_MIN,T2M,PRECTOTCORR"):
        assert part in url
    assert "time-standard" not in url  # the default is kept, as the sheet says


def test_first_pull_is_fetched_once_and_stored_unchanged(tmp_path, monkeypatch):
    monkeypatch.setattr(power, "FIRST_PULL", (START, END))
    body, calls = _body(), []

    def fetcher(url):
        calls.append(url)
        return body

    first = power.plan_first_pull(tmp_path, fetcher)
    second = power.plan_first_pull(tmp_path, fetcher)
    assert len(calls) == 1  # POWER can be reprocessed, so it is not asked twice
    (item,) = first
    assert item.path.read_bytes() == body and item.checks.ok
    assert item.manifest.evidence_type == "model_reanalysis" and item.manifest.sha256 == second[0].manifest.sha256
    assert "daily-point-api-v2.10.3" == item.manifest.version


def test_a_failed_response_blocks_the_item(tmp_path, monkeypatch):
    monkeypatch.setattr(power, "FIRST_PULL", (START, END))
    (item,) = power.plan_first_pull(tmp_path, lambda url: _body(drop="WS2M"))
    assert not item.checks.ok


def test_growing_season_summary_uses_april_to_november_only():
    parameter = {"T2M": {"20030115": -10.0, "20030615": 20.0, "20031215": -5.0},
                 "PRECTOTCORR": {"20030115": 99.0, "20030615": 3.0, "20031215": 99.0}}
    body = json.dumps({"properties": {"parameter": parameter}}).encode()
    assert power.growing_season_summary(body) == {2003: (20.0, 3.0)}


@pytest.mark.parametrize("lat,lon", [(power.MARSDEN_SITE["lat"], power.MARSDEN_SITE["lon"])])
def test_marsden_site_is_in_boone_county(lat, lon):
    assert 41.9 < lat < 42.2 and -94.1 < lon < -93.6


def test_full_run_asks_once_per_field_plus_the_marsden_site(tmp_path, monkeypatch):
    monkeypatch.setattr(power, "FULL_PERIOD", (START, END))
    calls = []

    def fetcher(url):
        calls.append(url)
        return _body()

    items = power.plan_full(tmp_path, fetcher, pause=0)
    assert len(items) == 46 and len(calls) == 46 and all(i.checks.ok for i in items)
    names = {i.path.name for i in items}
    assert "marsden-site_20030101-20030105.json" in names and "primary-001_20030101-20030105.json" in names
    assert all("GWET" not in c for c in calls)  # DS2 said nothing reads those variables
    power.plan_full(tmp_path, fetcher, pause=0)
    assert len(calls) == 46  # saved files are reused, not requested again
