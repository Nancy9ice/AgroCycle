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
