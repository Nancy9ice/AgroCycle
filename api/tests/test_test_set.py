from fastapi.testclient import TestClient

from api.core.test_set import build_test_set
from api.main import create_app
from api.settings import Settings


def row(field_id, scenario, outcome, label, ds1, role="test"):
    return {"field_id": field_id, "scenario": scenario, "outcome": outcome, "crop_history_summary": "s",
            "rules_version": "v1", "run_id": "r1", "role": role, "county": "Story",
            "field_class": ds1, "selection_label": label}


ROWS = [
    row("a", "every_constraint_stated", "strategy_worth_exploring", "rotation", "rotation"),
    row("a", "nothing_stated", "qualified_comparison", "rotation", "rotation"),
    row("b", "every_constraint_stated", "abstention", "mixed", "continuous_corn"),
    row("c", "every_constraint_stated", "strategy_worth_exploring", "pasture", "pasture_hay"),
]


def test_no_rows_is_none():
    assert build_test_set([], "dv") is None


def test_build_counts_matches_and_cdl_agreement():
    out = build_test_set(ROWS, "dv")
    assert out.outcome_counts == {"strategy_worth_exploring": 2, "abstention": 1}
    by_id = {f.field_id: f for f in out.fields}
    assert by_id["a"].match and by_id["b"].match and not by_id["c"].match
    assert len(by_id["a"].scenarios) == 2
    assert out.match_count == 2
    metrics = out.cdl_agreement.metrics
    assert (metrics["fields_compared"], metrics["fields_agreeing"]) == (3, 2)
    assert metrics["disagreements"][0] == {"selection_label": "mixed", "ds1_class": "continuous_corn", "fields": 1}


def test_endpoint_503_when_nothing_loaded(repository):
    client = TestClient(create_app(Settings(), repository))
    assert client.get("/api/v1/validation/test-set").status_code == 503


def test_endpoint_serves_audit(repository):
    class Repo:
        def __getattr__(self, name):
            return getattr(repository, name)
        def get_test_set_rows(self):
            return ROWS
    client = TestClient(create_app(Settings(), Repo()))
    body = client.get("/api/v1/validation/test-set").json()
    assert body["engine_version"] == "v1" and len(body["fields"]) == 3


DS1 = {
    "run_id": "ds1_handover",
    "rules_version": "2026-11-14.1",
    "by_field": {"a": "strategy_worth_exploring", "b": "abstention", "c": "abstention"},
}


def test_ds1s_expected_outcomes_are_used_instead_of_the_derived_guess():
    out = build_test_set(ROWS, "dv", DS1)
    by_id = {f.field_id: f for f in out.fields}
    # "c" is a pasture field the selection label would call abstention, and DS1 agrees; the engine said
    # worth exploring, so it is a real mismatch now. "a" and "b" match DS1's expectation.
    assert [by_id[i].expected_outcome for i in "abc"] == ["strategy_worth_exploring", "abstention", "abstention"]
    assert [by_id[i].match for i in "abc"] == [True, True, False]
    assert out.expected_source == "ds1_expected"
    assert "ds1_handover" in out.expected_basis and "2026-11-14.1" in out.expected_basis
    assert "DS1's handover" in out.caveats[0] and "not ground truth" in out.caveats[0]


def test_it_falls_back_to_the_selection_label_when_no_expected_outcomes_are_loaded():
    out = build_test_set(ROWS, "dv", None)
    assert out.expected_source == "selection_label" and out.expected_basis == ""
    assert "No expected outcomes were loaded" in out.caveats[0]


def test_a_field_ds1_did_not_cover_falls_back_per_field_and_says_so():
    partial = {**DS1, "by_field": {"a": "strategy_worth_exploring"}}
    out = build_test_set(ROWS, "dv", partial)
    assert out.expected_source == "mixed"
    assert "most fields" in out.caveats[0]


def test_expected_rows_are_never_mistaken_for_an_engine_run():
    only_expected = [
        row("a", "expected", "strategy_worth_exploring", "rotation", "rotation"),
        row("b", "expected", "abstention", "mixed", "continuous_corn"),
    ]
    assert build_test_set(only_expected, "dv", DS1) is None  # no engine result: nothing to compare

    mixed_in = ROWS + only_expected
    out = build_test_set(mixed_in, "dv", DS1)
    assert {s.scenario for f in out.fields for s in f.scenarios} == {"every_constraint_stated", "nothing_stated"}


def test_endpoint_is_503_not_an_empty_200_when_only_expected_rows_exist(repository):
    class Repo:
        def __getattr__(self, name):
            return getattr(repository, name)

        def get_test_set_rows(self):
            return []  # the engine run is gone; only DS1's expected rows remain in the table

        def get_expected_outcomes(self):
            return DS1

    client = TestClient(create_app(Settings(), Repo()))
    response = client.get("/api/v1/validation/test-set")
    assert response.status_code == 503 and "engine run" in response.json()["error"]["message"]


def test_endpoint_serves_the_comparison_with_ds1s_expectations(repository):
    class Repo:
        def __getattr__(self, name):
            return getattr(repository, name)

        def get_test_set_rows(self):
            return ROWS

        def get_expected_outcomes(self):
            return DS1

    body = TestClient(create_app(Settings(), Repo())).get("/api/v1/validation/test-set").json()
    assert body["expected_source"] == "ds1_expected" and body["match_count"] == 2
