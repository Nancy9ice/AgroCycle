from fastapi.testclient import TestClient

from api.core.test_set import build_test_set
from api.main import create_app
from api.settings import Settings


def row(field_id, scenario, outcome, label, ds1, role="test", expected="", state=""):
    return {
        "field_id": field_id, "scenario": scenario, "outcome": outcome, "crop_history_summary": "s",
        "rules_version": "v1", "run_id": "r1", "role": role, "county": "Story",
        "field_class": ds1, "selection_label": label, "expected_outcome": expected, "expected_review_state": state,
    }


H = "every_constraint_stated"
# Four cases carry an expectation written by DS2 (all awaiting review); everything else is blank on purpose.
ROWS = [
    row("a", H, "strategy_worth_exploring", "rotation", "rotation", role="primary",
        expected="strategy_worth_exploring", state="awaiting_review"),
    row("a", "no_manure", "qualified_comparison", "rotation", "rotation",
        expected="qualified_comparison", state="awaiting_review"),
    row("a", "nothing_stated", "qualified_comparison", "rotation", "rotation"),
    row("b", H, "abstention", "mixed", "continuous_corn", expected="abstention", state="awaiting_review"),
    row("c", H, "strategy_worth_exploring", "pasture", "pasture_hay"),
    row("d", H, "abstention", "rotation", "rotation", expected="strategy_worth_exploring", state="awaiting_review"),
]


def by_id(out):
    return {f.field_id: f for f in out.fields}


def test_no_engine_run_is_none():
    assert build_test_set([], "dv") is None


def test_an_expectation_is_used_only_where_ds2_wrote_one():
    out = by_id(build_test_set(ROWS, "dv"))
    assert (out["a"].expected_outcome, out["a"].match) == ("strategy_worth_exploring", True)
    assert (out["b"].expected_outcome, out["b"].match) == ("abstention", True)
    # No expectation is not a failure and is not filled in from the field's class: that would be circular.
    assert (out["c"].expected_outcome, out["c"].match) == (None, None)


def test_a_real_disagreement_is_still_reported():
    assert by_id(build_test_set(ROWS, "dv"))["d"].match is False


def test_the_review_state_travels_with_every_expectation_and_with_none_without():
    out = by_id(build_test_set(ROWS, "dv"))
    assert out["a"].expected_review_state == "awaiting_review" and out["c"].expected_review_state is None


def test_a_field_can_have_an_expectation_for_one_scenario_and_not_another():
    scenarios = {s.scenario: s for s in by_id(build_test_set(ROWS, "dv"))["a"].scenarios}
    assert scenarios["no_manure"].expected_outcome == "qualified_comparison" and scenarios["no_manure"].match is True
    assert scenarios["nothing_stated"].expected_outcome is None and scenarios["nothing_stated"].match is None


def test_the_summary_counts_cases_and_says_they_are_awaiting_review():
    s = build_test_set(ROWS, "dv").expectations
    assert (s.cases_total, s.cases_with_expectation, s.cases_matching) == (6, 4, 3)
    assert (s.fields_with_expectation, s.awaiting_review, s.reviewed) == (3, 4, 0)
    assert "Only 4 of 6 cases have an expectation" in s.note
    assert "circular" in s.note and "4 of the 4 are still awaiting review" in s.note and "not yet a benchmark" in s.note


def test_once_reviewed_the_note_says_so():
    reviewed = [{**r, "expected_review_state": "reviewed" if r["expected_outcome"] else ""} for r in ROWS]
    note = build_test_set(reviewed, "dv").expectations.note
    assert "All have been reviewed" in note and "awaiting review" not in note


def test_a_run_with_no_expectations_says_there_is_nothing_to_compare_and_gives_no_verdict():
    blank = [{**r, "expected_outcome": "", "expected_review_state": ""} for r in ROWS]
    out = build_test_set(blank, "dv")
    assert out.expectations.cases_with_expectation == 0 and "nothing to compare" in out.expectations.note
    assert all(f.match is None for f in out.fields)


def test_rows_from_older_loads_without_the_expectation_columns_still_work():
    old = [{k: v for k, v in r.items() if not k.startswith("expected")} for r in ROWS]
    assert build_test_set(old, "dv").expectations.cases_with_expectation == 0


def test_outcome_counts_and_cdl_agreement_are_unchanged():
    out = build_test_set(ROWS, "dv")
    assert out.outcome_counts == {"strategy_worth_exploring": 2, "abstention": 2}
    metrics = out.cdl_agreement.metrics
    assert metrics["fields_compared"] == 4 and metrics["fields_agreeing"] == 3
    assert metrics["disagreements"][0] == {"selection_label": "mixed", "ds1_class": "continuous_corn", "fields": 1}
    assert "not accuracy" in out.cdl_agreement.note


def test_ds1s_handover_rows_are_never_taken_for_an_engine_result():
    handover = [row("a", "expected", "strategy_worth_exploring", "rotation", "rotation")]
    assert build_test_set(handover, "dv") is None
    out = build_test_set(ROWS + handover, "dv")
    assert {s.scenario for f in out.fields for s in f.scenarios} == {H, "no_manure", "nothing_stated"}


def test_the_caveats_never_present_a_blank_as_a_failure():
    text = " ".join(build_test_set(ROWS, "dv").caveats)
    assert "A field with no expectation is not a failure" in text and "demonstration polygons" in text


class Repo:
    def __init__(self, repository, rows):
        self._base, self.rows = repository, rows

    def __getattr__(self, name):
        return getattr(self._base, name)

    def get_test_set_rows(self):
        if isinstance(self.rows, Exception):
            raise self.rows
        return self.rows


def client(repository, rows):
    return TestClient(create_app(Settings(), Repo(repository, rows)))


def test_endpoint_serves_the_audit_with_its_expectation_summary(repository):
    body = client(repository, ROWS).get("/api/v1/validation/test-set").json()
    assert body["expectations"]["cases_with_expectation"] == 4 and body["expectations"]["awaiting_review"] == 4
    assert {f["field_id"]: f["match"] for f in body["fields"]} == {"a": True, "b": True, "c": None, "d": False}
    assert "match_count" not in body and "expected_source" not in body  # the old derived-expectation fields are gone


def test_endpoint_is_503_when_there_is_no_engine_run_or_it_cannot_be_read(repository):
    assert client(repository, []).get("/api/v1/validation/test-set").status_code == 503
    only_expected = [row("a", "expected", "abstention", "rotation", "rotation")]
    response = client(repository, only_expected).get("/api/v1/validation/test-set")
    assert response.status_code == 503 and "engine run" in response.json()["error"]["message"]
    assert client(repository, RuntimeError("down")).get("/api/v1/validation/test-set").status_code == 503


def test_without_the_database_it_says_so(repository):
    assert TestClient(create_app(Settings(), repository)).get("/api/v1/validation/test-set").status_code == 503
