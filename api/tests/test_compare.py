import json

import pytest
from fastapi.testclient import TestClient

from api.core.profile import build_profile
from api.core.serialise import to_plain
from api.db.repository import FileRepository
from api.main import create_app
from api.settings import Settings
from engine import decision as engine

ALL_YES = {
    "manure_access": True,
    "forage_use_or_buyer": True,
    "oat_use_or_buyer": True,
    "small_grain_equipment_or_contractor": True,
}


def post(client, field_id="primary-001", **body):
    return client.post(f"/api/v1/fields/{field_id}/compare", json=body)


def test_unknown_field_is_404(client):
    assert post(client, "nope").status_code == 404


def test_unknown_priority_and_extra_keys_are_422(client):
    assert post(client, priorities=["profit"]).status_code == 422
    assert post(client, profile={"county": "Story"}).status_code == 422


@pytest.mark.parametrize("answer", ["yes", "true", "unsure", 1, 0, "false"])
def test_an_answer_that_is_not_true_false_or_null_is_rejected_not_interpreted(client, answer):
    # Pydantic's default would coerce "yes" or 1 to True, which would turn a guess into a farmer's answer.
    assert post(client, manure_access=answer).status_code == 422


def test_a_rotation_field_abstains_today_because_no_indicator_is_computed(client):
    body = post(client).json()
    decision = body["decision"]
    assert decision["outcome"] == "abstention"
    assert body["preview"] is False
    for indicator in engine.REQUIRED_INDICATORS:
        assert f"indicator {indicator}" in decision["unknowns"]


@pytest.mark.parametrize("field_id", ["test-027", "test-033", "test-039"])
def test_a_field_outside_the_domain_abstains_and_offers_no_option(client, field_id):
    decision = post(client, field_id, **ALL_YES, sample_indicators=True).json()["decision"]
    assert decision["outcome"] == "abstention"
    assert {s["feasibility"] for s in decision["strategies"]} == {"unavailable"}


def test_unanswered_stays_unknown_and_is_returned_as_null(client):
    decision = post(client, manure_access=False).json()["decision"]
    recorded = decision["constraints_recorded"]
    assert recorded["manure_access"] is False
    assert recorded["oat_use_or_buyer"] is None
    assert "oat_use_or_buyer" in decision["unknowns"]


def test_sample_preview_reaches_all_three_outcomes(client):
    outcomes = {
        post(client, sample_indicators=True, **ALL_YES).json()["decision"]["outcome"],
        post(client, sample_indicators=True).json()["decision"]["outcome"],
        post(client, "test-027", sample_indicators=True).json()["decision"]["outcome"],
    }
    assert outcomes == {"strategy_worth_exploring", "qualified_comparison", "abstention"}


def test_the_response_says_when_it_is_a_preview(client):
    assert post(client, sample_indicators=True).json()["preview"] is True


def test_sample_preview_can_be_switched_off(repository):
    locked = TestClient(create_app(Settings(allow_sample_preview=False), repository))
    assert post(locked, sample_indicators=True).status_code == 403
    assert post(locked).status_code == 200


def test_the_response_equals_the_engine_for_the_same_inputs(client, repository):
    record = repository.get_field("primary-001")
    expected = to_plain(
        engine.assess(
            build_profile(record, repository.get_indicators("primary-001"), sample_indicators=True),
            engine.FarmerConstraints.from_mapping({**ALL_YES, "manure_access": False, "priorities": ["soil"]}),
        )
    )
    actual = post(
        client, sample_indicators=True, **{**ALL_YES, "manure_access": False}, priorities=["soil"]
    ).json()["decision"]
    assert actual == json.loads(json.dumps(expected))


def test_real_indicator_outputs_let_the_engine_leave_abstention(indicator_dir):
    client = TestClient(create_app(Settings(), FileRepository(indicators_dir=indicator_dir)))
    decision = post(client, **ALL_YES).json()["decision"]
    assert decision["unknowns"] == []
    assert decision["outcome"] == "strategy_worth_exploring"
    # The dominant drainage class ("Poorly drained") is known and shown as known. DS2 withdrew the
    # alfalfa-drainage rule on 2026-11-15 for lack of a source, so it no longer qualifies option C.
    feasibility = {s["strategy_id"]: s["feasibility"] for s in decision["strategies"]}
    assert feasibility["B"] == "available" and feasibility["C"] == "available"


def test_priorities_are_recorded_and_change_nothing(client):
    base = post(client, sample_indicators=True, **ALL_YES).json()["decision"]
    with_priorities = post(
        client, sample_indicators=True, priorities=["soil", "inputs"], **ALL_YES
    ).json()["decision"]
    assert with_priorities["priorities_recorded"] == ["soil", "inputs"]
    assert with_priorities["outcome"] == base["outcome"]
    assert [o["status"] for o in with_priorities["outcomes"]] == [o["status"] for o in base["outcomes"]]


def test_the_result_has_no_score_rank_or_winner(client):
    def keys(value):
        if isinstance(value, dict):
            for key, item in value.items():
                yield key
                yield from keys(item)
        elif isinstance(value, list):
            for item in value:
                yield from keys(item)

    names = {key.lower() for key in keys(post(client, sample_indicators=True).json())}
    for banned in ("score", "rank", "winner", "best", "recommendation", "weight"):
        assert not [name for name in names if banned in name], banned


def test_fields_and_health(client):
    assert len(client.get("/api/v1/fields").json()) == 45
    assert client.get("/api/v1/fields/primary-001").json()["field_class"] == "rotation"
    health = client.get("/api/v1/health").json()
    assert health["status"] == "ok" and health["data_source"] == "files"
    assert client.get("/api/v1/fields/nope").status_code == 404


def test_openapi_describes_the_compare_endpoint(client):
    schema = client.get("/openapi.json").json()
    assert "/api/v1/fields/{field_id}/compare" in schema["paths"]
    assert all(path.startswith("/api/v1/") for path in schema["paths"])  # no unversioned endpoints
    assert "DecisionOut" in schema["components"]["schemas"]


def test_compare_says_when_the_analysis_is_only_in_memory(client):
    body = post(client).json()  # file mode keeps analyses in memory
    assert body["persistence"] == "temporary"
    assert "memory" in body["persistence_warning"]


def test_compare_says_when_the_analysis_could_not_be_saved(repository):
    class Failing:
        durable_analyses = True

        def __getattr__(self, name):
            return getattr(repository, name)

        def store_analysis(self, **_):
            raise RuntimeError("clickhouse down")

    failing = TestClient(create_app(Settings(), Failing()))
    body = failing.post("/api/v1/fields/primary-001/compare", json={}).json()
    assert body["persistence"] == "failed"
    assert "could not be saved" in body["persistence_warning"]
    assert body["decision"]  # the comparison itself is still returned


def test_a_drawn_boundary_is_validated_but_not_comparable(client):
    square = {"type": "Polygon", "coordinates": [[[-93.5, 42.0], [-93.49, 42.0], [-93.49, 42.01], [-93.5, 42.01], [-93.5, 42.0]]]}
    body = client.post("/api/v1/fields", json={"geometry": square}).json()
    assert body["valid"] and body["can_compare"] is False
    assert "demonstration field" in body["message"]
    assert client.post(f"/api/v1/fields/{body['field_id']}/compare", json={}).status_code == 404
    demo = client.post("/api/v1/fields", json={"demo_field_id": "primary-001"}).json()
    assert demo["can_compare"] is True and demo["message"] is None


def test_context_answers_are_recorded_but_never_change_the_outcome(client):
    base = post(client, **ALL_YES).json()
    with_context = post(
        client, **ALL_YES, context={"hay_equipment_or_contractor": False, "storage_space": False, "extra_labour": "little"}
    ).json()
    assert with_context["decision"] == base["decision"]  # no rule reads them
    assert with_context["context_recorded"] == {
        "hay_equipment_or_contractor": False, "storage_space": False, "extra_labour": "little",
    }
    assert "do not change the result" in with_context["context_note"]
    assert base["context_recorded"] == {
        "hay_equipment_or_contractor": None, "storage_space": None, "extra_labour": None,
    }


def test_context_answers_are_strict(client):
    assert post(client, context={"storage_space": "yes"}).status_code == 422
    assert post(client, context={"extra_labour": "lots"}).status_code == 422
    assert post(client, context={"unknown_key": True}).status_code == 422


def test_ask_context_labels_context_answers_as_unused_by_the_rules():
    from api.core.ask import build_analysis_context

    analysis = {
        "field": {"field_id": "f"}, "decision": {},
        "context_recorded": {"hay_equipment_or_contractor": False, "storage_space": None, "extra_labour": "some"},
    }
    text, _ = build_analysis_context(analysis, [])
    assert "NO rule uses these" in text and "Extra labour at busy times: some" in text


def test_demo_fields_carry_what_the_map_and_list_need(client):
    fields = client.get("/api/v1/fields/demo").json()
    assert len(fields) == 45
    primary = next(f for f in fields if f["field_id"] == "primary-001")
    assert primary["field_class"] == "rotation" and primary["domain_note"].startswith("in-domain")
    assert "demonstration geometry" in primary["provenance"]
    lon, lat = primary["centroid"]
    assert -94 < lon < -93 and 41.5 < lat < 42.5


def test_pilot_area_serves_both_county_outlines(client):
    body = client.get("/api/v1/meta/pilot-area").json()
    assert sorted(c["county"] for c in body["counties"]) == ["Boone", "Story"]
    ring = body["counties"][0]["ring"]
    assert ring[0] == ring[-1] and len(ring) > 10


class TestPrioritiesShapeTheComparison:
    """DS2's engine.emphasis through the API: priorities reorder and annotate, and cannot change the result."""

    def run(self, client, **extra):
        return post(client, **ALL_YES, sample_indicators=True, **extra).json()

    def test_a_water_first_farmer_sees_the_water_outcomes_first_and_is_told_what_we_cannot_measure(self, client):
        out = self.run(client, priority_levels={"water": "high"})
        emphasis = out["emphasis"]
        assert emphasis["highlighted"][0] == "nitrate_leaching_reduction"
        assert emphasis["outcome_order"][: len(emphasis["highlighted"])] == emphasis["highlighted"]
        assert emphasis["priorities_used"] == ["water"]
        assert "Nothing here measures water leaving your soil" in emphasis["gaps_for_priorities"][0]

    def test_priorities_never_change_the_result_or_hide_an_outcome(self, client):
        plain = self.run(client)
        shaped = self.run(client, priority_levels={"soil": "high", "income": "high", "forage": "medium"})
        assert shaped["decision"]["outcome"] == plain["decision"]["outcome"]
        assert shaped["decision"]["outcome_reason"] == plain["decision"]["outcome_reason"]
        assert shaped["decision"]["strategies"] == plain["decision"]["strategies"]
        ids = [o["outcome_id"] for o in plain["decision"]["outcomes"]]
        assert sorted(shaped["emphasis"]["outcome_order"]) == sorted(ids)  # all of them, only reordered

    def test_no_priorities_gives_the_engines_own_order_and_no_gaps(self, client):
        out = self.run(client)
        ids = [o["outcome_id"] for o in out["decision"]["outcomes"]]
        assert out["emphasis"]["outcome_order"] == ids
        assert out["emphasis"]["highlighted"] == [] and out["emphasis"]["gaps_for_priorities"] == []

    def test_low_is_an_answer_not_a_request_and_promotes_nothing(self, client):
        out = self.run(client, priority_levels={"soil": "low", "water": "low"})
        assert out["emphasis"]["highlighted"] == [] and out["emphasis"]["priorities_used"] == []

    def test_medium_promotes_like_high(self, client):
        out = self.run(client, priority_levels={"forage": "medium"})
        assert out["emphasis"]["highlighted"] == ["forage_supply"]
        assert "forage yield, quality or feed value" in out["emphasis"]["gaps_for_priorities"][0]

    def test_the_older_priorities_list_still_works_and_means_high(self, client):
        legacy = self.run(client, priorities=["soil"])
        modern = self.run(client, priority_levels={"soil": "high"})
        assert legacy["emphasis"]["highlighted"] == modern["emphasis"]["highlighted"]
        assert legacy["decision"]["priorities_recorded"] == ["soil"]

    def test_the_new_levels_win_where_both_name_a_priority(self, client):
        out = self.run(client, priorities=["soil"], priority_levels={"soil": "low"})
        assert out["emphasis"]["highlighted"] == []

    def test_only_high_priorities_are_recorded_on_the_decision(self, client):
        out = self.run(client, priority_levels={"soil": "high", "water": "medium", "inputs": "low"})
        assert out["decision"]["priorities_recorded"] == ["soil"]

    def test_there_is_no_score_rank_winner_or_weight_anywhere_in_it(self, client):
        out = self.run(client, priority_levels={"soil": "high"})
        keys = set(out["emphasis"])
        assert keys == {"outcome_order", "highlighted", "gaps_for_priorities", "priorities_used", "note"}
        assert not any(word in k for k in keys for word in ("score", "rank", "winner", "weight"))
        assert "do not change the result" in out["emphasis"]["note"]

    @pytest.mark.parametrize("bad", [{"soil": "very high"}, {"colour": "high"}, {"soil": 3}])
    def test_an_unknown_level_or_priority_is_refused(self, client, bad):
        assert post(client, priority_levels=bad).status_code == 422

    def test_a_saved_result_keeps_its_emphasis(self, client):
        made = self.run(client, priority_levels={"water": "high"})
        saved = client.get(f"/api/v1/analyses/{made['analysis_id']}").json()
        assert saved["emphasis"] == made["emphasis"]
