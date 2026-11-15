from fastapi.testclient import TestClient

from api.core.rule_register import build_rule_register
from api.main import create_app
from api.settings import Settings

RAW = {
    "rules_version": "v1",
    "rules": [
        {"rule_id": "r1", "applies_to": "all_outcomes", "context_key": "gdd", "operator": "gt", "value": "300.0",
         "effect": "qualified", "condition_text": "c", "rationale": "r", "evidence_basis": "team_proposed",
         "review": "not_expert_reviewed"},
        {"rule_id": "r2", "applies_to": "applied_n_reduction", "context_key": "manure", "operator": "equals",
         "value": "false", "effect": "out_of_domain", "condition_text": "c", "rationale": "r",
         "evidence_basis": "experimental_context", "review": "not_expert_reviewed"},
        {"rule_id": "r3", "applies_to": "all_outcomes", "context_key": "county", "operator": "not_in",
         "value": '["Story", "Boone"]', "effect": "qualified", "condition_text": "c", "rationale": "r",
         "evidence_basis": "team_proposed", "review": "not_expert_reviewed"},
    ],
    "crop_claims": [
        {"claim_id": "c1", "crop": "alfalfa, oat", "claim": "x", "status": "research_needed",
         "evidence_type": "", "source": "", "note": "n"},
        {"claim_id": "c2", "crop": "red_clover", "claim": "y", "status": "sourced",
         "evidence_type": "experimental", "source": "Davis 2012", "note": ""},
    ],
    "outcomes": [
        {"outcome_id": "o1", "label": "L", "claimable": 0, "evidence_type": "", "source": "", "statement": "",
         "caution": "c", "caution_reference": "r"},
    ],
    "strategies": [
        {"strategy_id": "A", "label": "Two-year", "rotation": "maize-soybean", "phases": '["maize", "soybean"]',
         "why_included": "w", "operational_requirements": '["Equipment"]', "evidence_anchor": "Davis"},
    ],
}


def test_nothing_loaded_is_none():
    assert build_rule_register(None, "v1", "dv") is None
    assert build_rule_register({"rules_version": "v1", "rules": []}, "v1", "dv") is None


def test_register_counts_decodes_json_columns_and_says_nothing_is_expert_reviewed():
    out = build_rule_register(RAW, "v1", "dv")
    s = out.summary
    assert (s.rules_total, s.rules_team_proposed, s.rules_experimental_context, s.rules_expert_reviewed) == (3, 2, 1, 0)
    assert (s.claims_total, s.claims_sourced, s.claims_research_needed) == (2, 1, 1)
    by_id = {r.rule_id: r for r in out.rules}
    assert by_id["r1"].value == 300.0 and by_id["r2"].value is False and by_id["r3"].value == ["Story", "Boone"]
    assert out.crop_claims[0].crops == ["alfalfa", "oat"]
    assert out.outcomes[0].claimable is False
    assert out.strategies[0].phases == ["maize", "soybean"]
    assert out.strategies[0].operational_requirements == ["Equipment"]
    text = " ".join(out.caveats)
    assert "No rule has been reviewed by an agronomist" in text
    assert "2 of 3 rules are team-proposed" in text and "1 of 2 crop claims have no source" in text
    assert out.matches_engine is True


def test_an_expert_review_removes_the_no_review_caveat():
    raw = {**RAW, "rules": [{**RAW["rules"][0], "review": "expert_reviewed"}]}
    out = build_rule_register(raw, "v1", "dv")
    assert out.summary.rules_expert_reviewed == 1
    assert "No rule has been reviewed" not in " ".join(out.caveats)


def test_a_stale_register_is_flagged():
    out = build_rule_register(RAW, "v2", "dv")
    assert out.matches_engine is False and "out of date" in " ".join(out.caveats)


def test_endpoint_503_when_nothing_loaded(repository):
    client = TestClient(create_app(Settings(), repository))  # file mode has no register
    assert client.get("/api/v1/evidence/rules").status_code == 503


def test_endpoint_serves_the_register_and_a_read_failure_is_503(repository):
    class Repo:
        raw = RAW

        def __getattr__(self, name):
            return getattr(repository, name)

        def get_rule_register(self):
            if self.raw is None:
                raise RuntimeError("clickhouse down")
            return self.raw

    repo = Repo()
    client = TestClient(create_app(Settings(), repo))
    body = client.get("/api/v1/evidence/rules").json()
    assert body["rules_version"] == "v1" and len(body["rules"]) == 3 and body["summary"]["claims_sourced"] == 1
    repo.raw = None
    assert client.get("/api/v1/evidence/rules").status_code == 503
