import json

import pytest

from ingest import nass
from ingest.subset import SizeBudgetExceededError


def _row(county="STORY", commodity="CORN", statistic="YIELD", year=2020, value="190.1"):
    return {"commodity_desc": commodity, "statisticcat_desc": statistic, "unit_desc": "BU / ACRE",
            "county_code": nass.COUNTIES[county], "state_alpha": "IA", "year": str(year),
            "Value": value, "short_desc": f"{commodity} - {statistic}", "freq_desc": "ANNUAL",
            "reference_period_desc": "YEAR"}


def _body(rows):
    return json.dumps({"data": rows}).encode()


def _fake(rows_for=lambda params: [_row(params["county_name"], params["commodity_desc"],
                                         params["statisticcat_desc"])], empty=()):
    calls = []

    def fetcher(params):
        calls.append(params)
        if (params["commodity_desc"], params["statisticcat_desc"]) in empty:
            raise nass.NoDataError("none")
        return _body(rows_for(params))

    fetcher.calls = calls
    return fetcher


def test_a_good_response_passes_and_counts_withheld_values():
    body = _body([_row(), _row(year=2021, value="(D)")])
    result, summary = nass.inspect(body, "STORY", "CORN", "YIELD")
    assert result.ok and summary["rows"] == 2 and summary["suppressed"] == 1
    assert summary["years"] == [2020, 2021]


@pytest.mark.parametrize("row, text", [
    (_row(county="BOONE"), "not STORY"),
    (_row(commodity="OATS"), "not CORN"),
    (_row(year=1999), "outside"),
    ({"Value": "1"}, "missing"),
])
def test_wrong_rows_are_reported(row, text):
    result, _ = nass.inspect(_body([row]), "STORY", "CORN", "YIELD")
    assert any(text in p for p in result.problems)


def test_garbage_and_empty_responses_are_rejected():
    assert not nass.inspect(b"<html>", "STORY", "CORN", "YIELD")[0].ok
    assert not nass.inspect(_body([]), "STORY", "CORN", "YIELD")[0].ok


def test_the_manifest_url_never_holds_the_key():
    url = nass.public_url(nass.query_params("STORY", "CORN", "YIELD"))
    assert "<NASS_API_KEY>" in url or "%3CNASS_API_KEY%3E" in url
    assert "county_name=STORY" in url and "year__GE=2003" in url


def test_plan_makes_one_item_per_request_and_caches(tmp_path):
    fetcher = _fake()
    items = nass.plan(tmp_path, fetcher, pause=0)
    assert len(items) == 2 * 4 * 4 and all(i.checks.ok for i in items)
    assert all(i.manifest.evidence_type == "survey" for i in items)
    again = nass.plan(tmp_path, _fake(), pause=0)  # saved files are reused, nothing re-fetched
    assert len(again) == len(items)


def test_requests_with_no_data_are_listed_not_filled(tmp_path):
    items = nass.plan(tmp_path, _fake(empty={("HAY", "YIELD")}), pause=0)
    listing = next(i for i in items if i.path.name == nass.EMPTY_NAME)
    entries = json.loads(listing.path.read_text())["requests_with_no_data"]
    assert len(entries) == 2 and {e["commodity"] for e in entries} == {"HAY"}
    assert all("api_message" in e for e in entries)
    assert len(items) == 2 * 4 * 4 - 2 + 1


def test_all_requests_empty_is_an_error_not_an_empty_result(tmp_path):
    everything = {(c, s) for c in nass.COMMODITIES for s in nass.STATISTICS}
    with pytest.raises(RuntimeError, match="every NASS request"):
        nass.plan(tmp_path, _fake(empty=everything), pause=0)


def test_an_invalid_query_for_anything_but_hay_planted_is_an_error(tmp_path):
    def fetcher(params):
        if (params["commodity_desc"], params["statisticcat_desc"]) == ("OATS", "YIELD"):
            raise nass.NoDataError("bad request - invalid query")
        return _body([_row(params["county_name"], params["commodity_desc"], params["statisticcat_desc"])])

    with pytest.raises(RuntimeError, match="invalid query"):
        nass.plan(tmp_path, fetcher, pause=0)


def test_hay_planted_may_be_invalid_and_is_listed(tmp_path):
    items = nass.plan(tmp_path, _fake(empty={("HAY", "AREA PLANTED")}), pause=0)
    assert any(i.path.name == nass.EMPTY_NAME for i in items)


def test_a_stale_empty_list_is_removed_when_nothing_is_empty(tmp_path):
    (tmp_path / nass.EMPTY_NAME).write_text("{}")
    nass.plan(tmp_path, _fake(), pause=0)
    assert not (tmp_path / nass.EMPTY_NAME).exists()


def test_a_rejected_response_is_not_cached(tmp_path):
    bad = _fake(rows_for=lambda p: [_row(county="BOONE" if p["county_name"] == "STORY" else "STORY")])
    items = nass.plan(tmp_path, bad, pause=0)
    assert any(not i.checks.ok for i in items)
    assert not list(tmp_path.glob("*.json"))


def test_budget_is_enforced(tmp_path, monkeypatch):
    monkeypatch.setattr(nass, "BUDGET_BYTES", 10)
    with pytest.raises(SizeBudgetExceededError):
        nass.plan(tmp_path, _fake(), pause=0)
