import json
from typing import ClassVar

from fastapi.testclient import TestClient

from api.core.transition import build_transition
from api.main import create_app
from api.settings import Settings

NOT = "not established: no source gives timing for this phase"


def row(year, crop, timing=NOT, basis="experimental", needs=("The equipment you already have",), stress="season_stress"):
    return {
        "year": year, "crop": crop, "action": f"Grow {crop}.", "needs": json.dumps(list(needs)),
        "timing_note": timing, "stress_phase": stress, "evidence_basis": basis,
        "source": "Davis et al. (2012)", "rules_version": "2026-11-15.5",
    }


B_ROWS = [
    row(0, "manure", timing="Applied in October of each year (Text S1).", stress="", needs=("Access to composted manure",)),
    row(1, "corn"),
    row(2, "soybean"),
    row(3, "oat with red clover", basis="team_proposed"),
]


def test_nothing_loaded_is_none():
    assert build_transition("B", [], "dv") is None


def test_steps_come_in_order_with_timing_marked_as_established_only_where_it_is_sourced():
    out = build_transition("B", list(reversed(B_ROWS)), "dv")
    assert [s.year for s in out.steps] == [0, 1, 2, 3]
    manure, corn, _, oat = out.steps
    assert manure.timing_established is True and "October" in manure.timing_note
    assert corn.timing_established is False and corn.timing_note.startswith("not established")
    assert oat.timing_established is False
    assert out.rotation == "Three-year maize-soybean-oat/red clover"


def test_the_evidence_basis_and_the_weather_link_are_carried_as_given():
    out = build_transition("B", B_ROWS, "dv")
    assert [s.evidence_basis for s in out.steps] == ["experimental", "experimental", "experimental", "team_proposed"]
    assert [s.shows_past_weather for s in out.steps] == [False, True, True, True]  # the manure step is not a weather step
    assert out.steps[0].needs == ["Access to composted manure"]


def test_the_caveats_say_it_is_a_starting_point_and_that_timing_is_not_invented():
    text = " ".join(build_transition("B", B_ROWS, "dv").caveats)
    assert "not a final plan" in text and "no planting dates" in text and "October" in text
    assert "no cost, yield or profit" in text.lower()


def test_no_step_other_than_the_manure_names_a_month():
    months = ("january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december")
    out = build_transition("B", B_ROWS, "dv")
    for step in out.steps[1:]:
        assert not any(m in (step.action + step.timing_note).lower() for m in months)


class TestReadiness:
    constraints: ClassVar[dict] = {
        "manure_access": False, "small_grain_equipment_or_contractor": True,
        "oat_use_or_buyer": None, "forage_use_or_buyer": True,
    }

    def test_each_answer_is_yes_no_or_not_answered_never_a_guess(self):
        out = build_transition("B", B_ROWS, "dv", self.constraints)
        by_key = {r.constraint: r for r in out.readiness}
        assert by_key["manure_access"].status == "no" and by_key["manure_access"].answer is False
        assert by_key["small_grain_equipment_or_contractor"].status == "yes"
        assert by_key["oat_use_or_buyer"].status == "not_answered" and by_key["oat_use_or_buyer"].answer is None

    def test_the_forage_answer_only_bears_on_strategy_c(self):
        b = {r.constraint for r in build_transition("B", B_ROWS, "dv", self.constraints).readiness}
        c = {r.constraint for r in build_transition("C", B_ROWS, "dv", self.constraints).readiness}
        assert "forage_use_or_buyer" not in b and "forage_use_or_buyer" in c

    def test_each_answer_points_at_the_step_it_bears_on(self):
        out = build_transition("C", B_ROWS, "dv", self.constraints)
        assert {r.constraint: r.step_year for r in out.readiness}["manure_access"] == 0

    def test_without_an_analysis_there_is_no_readiness(self):
        assert build_transition("B", B_ROWS, "dv").readiness is None


class Repo:
    def __init__(self, repository, rows):
        self._base, self.rows = repository, rows

    def __getattr__(self, name):
        return getattr(self._base, name)

    def get_transition_steps(self, strategy_id):
        if isinstance(self.rows, Exception):
            raise self.rows
        return self.rows


def client(repository, rows):
    return TestClient(create_app(Settings(), Repo(repository, rows)))


def test_endpoint_serves_b_and_c_and_refuses_a(repository):
    api = client(repository, B_ROWS)
    body = api.get("/api/v1/strategies/b/transition").json()  # the id is case-insensitive
    assert body["strategy_id"] == "B" and len(body["steps"]) == 4 and body["readiness"] is None
    assert api.get("/api/v1/strategies/C/transition").status_code == 200
    refused = api.get("/api/v1/strategies/A/transition")
    assert refused.status_code == 404 and "you already run" in refused.json()["error"]["message"]
    assert api.get("/api/v1/strategies/Z/transition").status_code == 404


def test_endpoint_is_503_when_nothing_is_loaded_or_the_table_cannot_be_read(repository):
    assert client(repository, []).get("/api/v1/strategies/B/transition").status_code == 503
    assert client(repository, RuntimeError("down")).get("/api/v1/strategies/B/transition").status_code == 503


def test_endpoint_adds_readiness_from_a_saved_comparison_and_404s_an_unknown_one(repository):
    api = client(repository, B_ROWS)
    made = api.post("/api/v1/fields/primary-001/compare", json={"manure_access": False}).json()
    body = api.get(f"/api/v1/strategies/B/transition?analysis_id={made['analysis_id']}").json()
    by_key = {r["constraint"]: r for r in body["readiness"]}
    assert by_key["manure_access"]["status"] == "no" and by_key["oat_use_or_buyer"]["status"] == "not_answered"
    assert api.get("/api/v1/strategies/B/transition?analysis_id=a_missing").status_code == 404
