"""Tests for the decision engine (roadmap Phase 10 exit check).

The roadmap asks for four categories: in-domain, out-of-domain, missing data and abstention. They are the
first four sections here. The rest pin the honesty properties: unknown is not false, forbidden claims stay
forbidden, and nothing ranks the strategies.

Run from the repository root:  python -m pytest engine -q
"""
import pytest

from engine import decision as d
from engine.rules import strategy_rules as rules

ALL_INDICATORS_OK = dict.fromkeys(d.REQUIRED_INDICATORS, "ok")


def in_domain_profile(**overrides) -> d.FieldProfile:
    base = {
        "field_id": "primary-001",
        "boundary_source": "demo",
        "crop_history_summary": "maize-soybean every year 2015-2025 (CDL)",
        "county": "Story",
        "crop_history_is_maize_soybean": True,
        "gdd_season_difference_vs_marsden": 40.0,
        "frost_free_days": 165,
        "dominant_drainage_class": "Well drained",
        "indicator_statuses": ALL_INDICATORS_OK,
    }
    base.update(overrides)
    return d.FieldProfile(**base)


def complete_constraints(**overrides) -> d.FarmerConstraints:
    base = {
        "manure_access": True,
        "forage_use_or_buyer": True,
        "oat_use_or_buyer": True,
        "small_grain_equipment_or_contractor": True,
    }
    base.update(overrides)
    return d.FarmerConstraints(**base)


def outcome_by_id(result: d.Decision, outcome_id: str) -> d.OutcomeAssessment:
    return next(outcome for outcome in result.outcomes if outcome.outcome_id == outcome_id)


def strategy_by_id(result: d.Decision, strategy_id: str) -> d.StrategyAssessment:
    return next(s for s in result.strategies if s.strategy_id == strategy_id)


# --- 1. in domain --------------------------------------------------------------------------------
def test_a_complete_in_domain_field_is_worth_exploring():
    result = d.assess(in_domain_profile(), complete_constraints())
    assert result.outcome == "strategy_worth_exploring"
    assert "not a recommendation" in result.outcome_reason
    assert result.unknowns == ()
    assert [s.feasibility for s in result.strategies] == ["available", "available", "available"]


def test_in_domain_outcomes_carry_their_evidence_and_their_caution():
    result = d.assess(in_domain_profile(), complete_constraints())
    applied_n = outcome_by_id(result, "applied_n_reduction")
    assert applied_n.status == "in_domain"
    assert applied_n.evidence_type == "experimental"
    assert "74.5" in applied_n.statement
    assert "total n" in applied_n.caution.lower()

    yields = outcome_by_id(result, "yield_parity")
    assert yields.evidence_type == "published"
    assert "not reproduced" in yields.caution.lower()


def test_the_result_records_the_rules_version_and_the_standing_limitations():
    result = d.assess(in_domain_profile(), complete_constraints())
    assert result.rules_version == rules.RULES_VERSION
    assert any("one research site" in limitation for limitation in result.limitations)
    assert any("not expert-reviewed" in limitation for limitation in result.limitations)


# --- 2. out of domain ----------------------------------------------------------------------------
def test_a_field_that_is_not_maize_soybean_is_out_of_domain():
    result = d.assess(
        in_domain_profile(crop_history_is_maize_soybean=False), complete_constraints()
    )
    assert result.outcome == "abstention"
    assert "applicability_crop_history_baseline" in result.outcome_reason
    assert all(s.feasibility == "unavailable" for s in result.strategies)


def test_no_manure_removes_the_nitrogen_outcome_only():
    result = d.assess(in_domain_profile(), complete_constraints(manure_access=False))
    applied_n = outcome_by_id(result, "applied_n_reduction")
    herbicide = outcome_by_id(result, "herbicide_reduction")

    assert applied_n.status == "out_of_domain"
    assert applied_n.statement is None
    assert "applicability_manure_access_applied_n" in [f.rule_id for f in applied_n.findings]

    # PRD 7.6: the herbicide comparison is untouched by manure access.
    assert herbicide.status == "in_domain"
    assert herbicide.statement is not None
    assert herbicide.findings == ()
    assert result.outcome == "qualified_comparison"


def test_no_forage_outlet_removes_strategy_c_but_leaves_b():
    result = d.assess(in_domain_profile(), complete_constraints(forage_use_or_buyer=False))
    assert strategy_by_id(result, "C").feasibility == "unavailable"
    assert strategy_by_id(result, "B").feasibility == "available"
    assert result.candidate_strategies() == ("B",)
    assert result.outcome == "strategy_worth_exploring"


def test_a_field_outside_the_demo_counties_is_qualified_not_excluded():
    result = d.assess(in_domain_profile(county="Polk"), complete_constraints())
    assert result.outcome == "qualified_comparison"
    assert outcome_by_id(result, "applied_n_reduction").status == "qualified"
    assert outcome_by_id(result, "applied_n_reduction").statement is not None


def test_poor_drainage_qualifies_strategy_c_without_removing_it():
    result = d.assess(
        in_domain_profile(dominant_drainage_class="Poorly drained"), complete_constraints()
    )
    assert strategy_by_id(result, "C").feasibility == "qualified"
    assert "applicability_alfalfa_drainage" in [
        f.rule_id for f in strategy_by_id(result, "C").findings
    ]


# --- 3. missing data -----------------------------------------------------------------------------
def test_unstated_manure_access_abstains_rather_than_assuming_either_way():
    result = d.assess(in_domain_profile(), complete_constraints(manure_access=d.UNKNOWN))
    applied_n = outcome_by_id(result, "applied_n_reduction")
    assert applied_n.status == "abstained"
    assert applied_n.statement is None
    assert "applicability_manure_unknown_applied_n" in [f.rule_id for f in applied_n.findings]
    assert "manure_access" in result.unknowns


def test_an_unknown_constraint_is_not_read_as_no():
    unknown = d.assess(in_domain_profile(), complete_constraints(forage_use_or_buyer=d.UNKNOWN))
    stated_no = d.assess(in_domain_profile(), complete_constraints(forage_use_or_buyer=False))
    assert strategy_by_id(unknown, "C").feasibility == "qualified"
    assert strategy_by_id(stated_no, "C").feasibility == "unavailable"


def test_an_unknown_constraint_is_not_read_as_yes_either():
    unknown = d.assess(in_domain_profile(), complete_constraints(oat_use_or_buyer=d.UNKNOWN))
    stated_yes = d.assess(in_domain_profile(), complete_constraints(oat_use_or_buyer=True))
    assert strategy_by_id(unknown, "B").feasibility == "qualified"
    assert strategy_by_id(stated_yes, "B").feasibility == "available"


def test_a_missing_required_indicator_withholds_every_outcome():
    statuses = dict(ALL_INDICATORS_OK)
    statuses["gdd"] = "unknown"
    result = d.assess(in_domain_profile(indicator_statuses=statuses), complete_constraints())
    assert result.outcome == "abstention"
    assert all(
        outcome.status == "abstained" for outcome in result.outcomes if outcome.claimable
    )
    assert "indicator gdd" in result.unknowns


def test_an_unknown_climate_distance_qualifies_rather_than_passing():
    result = d.assess(
        in_domain_profile(gdd_season_difference_vs_marsden=d.UNKNOWN), complete_constraints()
    )
    assert result.outcome == "qualified_comparison"
    assert outcome_by_id(result, "herbicide_reduction").status == "qualified"


def test_unknown_crop_history_abstains_rather_than_excluding():
    result = d.assess(
        in_domain_profile(crop_history_is_maize_soybean=d.UNKNOWN), complete_constraints()
    )
    assert result.outcome == "abstention"
    assert "nothing to compare" in result.outcome_reason


# --- 4. abstention -------------------------------------------------------------------------------
def test_an_empty_profile_abstains_and_says_what_is_missing():
    bare = d.FieldProfile(
        field_id="test-042",
        boundary_source="demo",
        crop_history_summary="not classified",
    )
    result = d.assess(bare, d.FarmerConstraints())
    assert result.outcome == "abstention"
    assert len(result.unknowns) >= 8
    assert all(
        outcome.status in ("abstained", "not_assessed", "qualified") for outcome in result.outcomes
    )


def test_abstention_still_returns_the_full_structure():
    result = d.assess(
        in_domain_profile(crop_history_is_maize_soybean=False), complete_constraints()
    )
    assert len(result.strategies) == 3
    assert len(result.outcomes) == len(rules.OUTCOME_EVIDENCE)
    assert result.limitations
    assert result.crop_history_summary


# --- forbidden claims ----------------------------------------------------------------------------
@pytest.mark.parametrize(
    "outcome_id", ["soil_carbon_change", "erosion_reduction", "nitrate_leaching_reduction"]
)
def test_forbidden_outcomes_are_never_claimed_however_good_the_field_is(outcome_id):
    result = d.assess(in_domain_profile(), complete_constraints())
    outcome = outcome_by_id(result, outcome_id)
    assert outcome.status == "not_assessed"
    assert outcome.statement is None
    assert outcome.claimable is False
    assert outcome.caution


def test_forage_supply_is_not_claimed_even_with_a_buyer():
    result = d.assess(in_domain_profile(), complete_constraints(forage_use_or_buyer=True))
    assert outcome_by_id(result, "forage_supply").status == "not_assessed"


# --- no ranking, no score ------------------------------------------------------------------------
def test_the_decision_carries_no_score_and_no_winner():
    result = d.assess(in_domain_profile(), complete_constraints())
    fields = set(vars(result))
    for forbidden in ("score", "rank", "ranking", "winner", "best", "recommendation", "weight"):
        assert not any(forbidden in name for name in fields)


def test_every_strategy_is_returned_even_when_one_is_unavailable():
    result = d.assess(in_domain_profile(), complete_constraints(forage_use_or_buyer=False))
    assert [s.strategy_id for s in result.strategies] == ["A", "B", "C"]
    assert strategy_by_id(result, "C").operational_requirements


def test_priorities_are_recorded_but_do_not_change_the_outcome():
    # Acting on priorities without an explicit weighting would be the composite score PRD 8.5 forbids.
    without = d.assess(in_domain_profile(), complete_constraints())
    with_priorities = d.assess(
        in_domain_profile(), complete_constraints(priorities=("soil health", "forage"))
    )
    assert with_priorities.priorities_recorded == ("soil health", "forage")
    assert with_priorities.outcome == without.outcome


# --- rule evaluation mechanics -------------------------------------------------------------------
def test_unknown_has_no_truth_value():
    with pytest.raises(TypeError, match="no truth value"):
        bool(d.UNKNOWN)


def test_unknown_is_a_singleton():
    assert d.UNKNOWN is d._Unknown()


def test_every_context_key_the_table_uses_is_supplied():
    context = d.build_context(in_domain_profile(), complete_constraints())
    for rule in rules.APPLICABILITY_RULES:
        assert rule.context_key in context, f"{rule.rule_id} reads an unsupplied key"


def test_numeric_rules_reject_a_non_numeric_value():
    rule = next(r for r in rules.APPLICABILITY_RULES if r.operator == "gt")
    with pytest.raises(TypeError, match="numerically"):
        d.rule_applies(rule, {rule.context_key: "quite a lot"})


def test_an_unsupported_operator_raises():
    broken = rules.ApplicabilityRule(
        rule_id="broken",
        outcome_id="all_outcomes",
        context_key="county",
        operator="approximately",
        value="Story",
        effect="qualified",
        condition_text="",
        rationale="",
        evidence_basis="team_proposed",
    )
    with pytest.raises(ValueError, match="unsupported operator"):
        d.rule_applies(broken, {"county": "Story"})


def test_severity_ordering_takes_the_worst_finding():
    result = d.assess(
        in_domain_profile(county="Polk"), complete_constraints(manure_access=False)
    )
    # qualified (out of county) and out_of_domain (no manure) both hit applied_n: the worst wins.
    assert outcome_by_id(result, "applied_n_reduction").status == "out_of_domain"


def test_the_engine_is_deterministic():
    first = d.assess(in_domain_profile(), complete_constraints())
    second = d.assess(in_domain_profile(), complete_constraints())
    assert first == second


def test_fired_rules_are_returned_in_table_order():
    context = d.build_context(
        in_domain_profile(county="Polk"), complete_constraints(manure_access=False)
    )
    fired = [finding.rule_id for finding in d.fired_rules(context)]
    order = [rule.rule_id for rule in rules.APPLICABILITY_RULES]
    assert fired == [rule_id for rule_id in order if rule_id in fired]


# --- the frontend boundary ------------------------------------------------------------------------
# web/src/features/priorities/engine-context.ts emits boolean | null per key, where null means
# "not answered" or "Not sure". None must never reach a rule as a known value.
FRONTEND_KEYS = (
    "manure_access",
    "forage_use_or_buyer",
    "oat_use_or_buyer",
    "small_grain_equipment_or_contractor",
)


def test_the_engine_reads_the_frontends_key_names():
    assert set(FRONTEND_KEYS) == set(d.CONSTRAINT_KEYS)
    context = d.build_context(in_domain_profile(), complete_constraints())
    for key in FRONTEND_KEYS:
        assert key in context


def test_json_null_is_normalised_to_unknown():
    constraints = d.FarmerConstraints(
        manure_access=None,
        forage_use_or_buyer=None,
        oat_use_or_buyer=None,
        small_grain_equipment_or_contractor=None,
    )
    for key in FRONTEND_KEYS:
        assert getattr(constraints, key) is d.UNKNOWN


def test_an_all_null_form_does_not_produce_a_confident_answer():
    nulls = dict.fromkeys(FRONTEND_KEYS)
    result = d.assess(in_domain_profile(), d.FarmerConstraints.from_mapping(nulls))
    assert result.outcome != "strategy_worth_exploring"
    assert set(FRONTEND_KEYS) <= set(result.unknowns)
    assert outcome_by_id(result, "applied_n_reduction").status == "abstained"


def test_from_mapping_matches_a_directly_built_constraints_object():
    answers = {
        "manure_access": True,
        "forage_use_or_buyer": None,
        "oat_use_or_buyer": False,
        "small_grain_equipment_or_contractor": True,
        "priorities": ["soil", "forage"],
    }
    built = d.FarmerConstraints.from_mapping(answers)
    assert built.manure_access is True
    assert built.forage_use_or_buyer is d.UNKNOWN
    assert built.oat_use_or_buyer is False
    assert built.priorities == ("soil", "forage")


def test_from_mapping_treats_an_absent_key_as_unknown():
    built = d.FarmerConstraints.from_mapping({"manure_access": True})
    assert built.forage_use_or_buyer is d.UNKNOWN
    assert built.priorities == ()


def test_a_null_profile_value_is_also_normalised():
    profile = in_domain_profile(dominant_drainage_class=None, frost_free_days=None)
    assert profile.dominant_drainage_class is d.UNKNOWN
    assert profile.frost_free_days is d.UNKNOWN
