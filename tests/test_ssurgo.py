import json

import pytest

from ingest import ssurgo

WKT = "POLYGON ((-93.7 42.0, -93.6 42.0, -93.6 42.1, -93.7 42.1, -93.7 42.0))"


def _table(*rows):
    return json.dumps({"Table": [list(r) for r in rows]}).encode()


class FakeSda:
    """Answers each step's query with a small canned table and counts the calls."""

    def __init__(self, reject_a=False, no_map_units=False):
        self.calls, self.reject_a, self.no_map_units = [], reject_a, no_map_units

    def __call__(self, query):
        self.calls.append(query)
        if "STIntersection" in query and self.reject_a:
            raise RuntimeError("Soil Data Access rejected the query: HTTP 400")
        if "STIntersection" in query or "SDA_Get_Mukey" in query:
            if self.no_map_units:
                return _table(["mukey", "isect_wkt"])
            return _table(["mukey", "isect_wkt"], ["111", "POLYGON ((0 0, 1 0, 1 1, 0 0))"], ["222", "POLYGON ((0 0, 1 0, 1 1, 0 0))"])
        if "FROM mapunit" in query:
            cols = ssurgo.COMPONENT_COLUMNS.replace("mu.", "").replace("c.", "").split(", ")
            return _table(cols, ["111", "6", "Okoboji", "9001", "Okoboji", "85", "Yes", "0.5", "100", "Poorly drained", "B/D", "Yes", "x", "5"],
                          ["222", "7", "Clarion", "9002", "Clarion", "100", "Yes", "3", "90", "Well drained", "B", "No", "y", "5"])
        if "FROM chorizon" in query:
            return _table(["cokey", "chkey", "hzname", "hzdept_r"], ["9001", "1", "A", "0"])
        return _table(["areasymbol", "areaname", "saverest"], ["IA015", "Boone County, Iowa", "9/8/2026"])


def test_four_raw_files_are_saved_and_planned(tmp_path):
    sda = FakeSda()
    items = ssurgo.plan_field("primary-001", WKT, tmp_path, sda)
    assert [i.key_name for i in items] == [
        "primary-001/step_a_map_units.json", "primary-001/step_b_components.json",
        "primary-001/step_c_horizons.json", "primary-001/step_d_survey_areas.json",
    ]
    assert all(i.checks.ok for i in items) and all(i.manifest.evidence_type == "survey" for i in items)
    assert "STIntersection" in items[0].manifest.subset["query"]
    assert "'111','222'" in items[1].manifest.subset["query"]  # step B asks for the mukeys found in A


def test_a_second_run_does_not_ask_the_service_again(tmp_path):
    sda = FakeSda()
    ssurgo.plan_field("primary-001", WKT, tmp_path, sda)
    calls = len(sda.calls)
    ssurgo.plan_field("primary-001", WKT, tmp_path, sda)
    assert len(sda.calls) == calls


def test_a_rejected_main_query_falls_back_and_says_so(tmp_path):
    items = ssurgo.plan_field("primary-001", WKT, tmp_path, FakeSda(reject_a=True))
    route = items[0].manifest.subset["route"]
    assert "fallback" in route and "area_unknown" in route
    assert "SDA_Get_Mukey_from_intersection_with_WktWgs84" in items[0].manifest.subset["query"]


def test_a_field_with_no_map_units_fails_its_check(tmp_path):
    items = ssurgo.plan_field("primary-001", WKT, tmp_path, FakeSda(no_map_units=True))
    assert any("no map units" in p for p in items[0].checks.problems)


def test_a_non_table_response_is_rejected(tmp_path):
    def broken(query):
        return b"<html>service error</html>" if "FROM chorizon" in query else FakeSda()(query)

    items = ssurgo.plan_field("primary-001", WKT, tmp_path, broken)
    assert any("not a Soil Data Access table" in p for i in items for p in i.checks.problems)


def test_first_pull_uses_the_primary_field_polygon(tmp_path):
    sda = FakeSda()
    ssurgo.plan_first_pull(tmp_path, sda)
    assert sda.calls[0].count("POLYGON") == 2 and "STGeomFromText" in sda.calls[0]


@pytest.mark.parametrize("name", ["step_a_map_units.json", "step_d_survey_areas.json"])
def test_files_are_stored_under_the_field_folder(tmp_path, name):
    ssurgo.plan_field("primary-001", WKT, tmp_path, FakeSda())
    assert (tmp_path / "primary-001" / name).exists()


def test_every_field_gets_four_files_and_saved_fields_are_not_asked_again(tmp_path):
    fake = FakeSda()
    items = ssurgo.plan_all(tmp_path, fake, pause=0)
    assert len(items) == 45 * 4 and all(i.checks.ok for i in items)
    assert {i.key_name.split("/")[0] for i in items} >= {"primary-001", "test-044"}
    calls = len(fake.calls)
    ssurgo.plan_all(tmp_path, fake, pause=0)
    assert len(fake.calls) == calls
