"""Tests for the strategy and applicability rule table (roadmap Phase 9 exit check).

These are honesty tests as much as structural ones: they assert that the table cannot quietly acquire an
unsourced agronomic claim, a forbidden outcome, or a rule that over-reaches.

Run from the repository root:  python -m pytest engine -q
"""
import pytest

from engine.rules import strategy_rules as r


# --- strategy profiles ---------------------------------------------------------------------------
def test_three_strategies_match_the_prd_comparison():
    assert [profile.strategy_id for profile in r.STRATEGY_PROFILES] == ["A", "B", "C"]
    assert [len(profile.phases) for profile in r.STRATEGY_PROFILES] == [2, 3, 4]


def test_every_profile_is_complete():
    for profile in r.STRATEGY_PROFILES:
        assert profile.label
        assert profile.rotation
        assert profile.why_included
        assert profile.evidence_anchor
        assert profile.operational_requirements


def test_both_diversified_options_declare_the_manure_requirement():
    for profile in r.STRATEGY_PROFILES:
        if profile.strategy_id == "A":
            continue
        requirements = " ".join(profile.operational_requirements).lower()
        assert "manure" in requirements


# --- outcomes ------------------------------------------------------------------------------------
def test_forbidden_outcomes_are_present_and_closed():
    forbidden = {"soil_carbon_change", "erosion_reduction", "nitrate_leaching_reduction"}
    by_id = {outcome.outcome_id: outcome for outcome in r.OUTCOME_EVIDENCE}
    assert forbidden <= set(by_id)
    for outcome_id in forbidden:
        outcome = by_id[outcome_id]
        assert outcome.claimable is False
        assert outcome.evidence_type is None
        assert outcome.source is None


def test_claimable_outcomes_name_an_evidence_type_and_a_source():
    for outcome in r.OUTCOME_EVIDENCE:
        if not outcome.claimable:
            continue
        assert outcome.evidence_type in r.EVIDENCE_TYPES
        assert outcome.source


def test_every_outcome_carries_a_statement_a_caution_and_a_source_line():
    for outcome in r.OUTCOME_EVIDENCE:
        assert outcome.statement
        assert outcome.caution
        assert outcome.caution_reference


def test_reproduced_outcomes_are_experimental_and_published_ones_are_not():
    by_id = {outcome.outcome_id: outcome for outcome in r.OUTCOME_EVIDENCE}
    assert by_id["applied_n_reduction"].evidence_type == "experimental"
    assert by_id["herbicide_reduction"].evidence_type == "experimental"
    # Yields and net returns come from the paper; the supplement has no plot-level yield tables.
    assert by_id["yield_parity"].evidence_type == "published"
    assert by_id["profitability_parity"].evidence_type == "published"
    assert "not recalculated" in by_id["yield_parity"].caution.lower()


def test_applied_nitrogen_outcome_refuses_the_phrase_total_n():
    outcome = next(o for o in r.OUTCOME_EVIDENCE if o.outcome_id == "applied_n_reduction")
    assert "not a prediction for your field" in outcome.caution.lower()
    assert "74.5" in outcome.statement


def test_herbicide_outcome_separates_mass_from_toxicity():
    outcome = next(o for o in r.OUTCOME_EVIDENCE if o.outcome_id == "herbicide_reduction")
    assert "says nothing about how harmful" in outcome.caution.lower()


def test_profitability_is_not_computed_by_agrocycle():
    outcome = next(o for o in r.OUTCOME_EVIDENCE if o.outcome_id == "profitability_parity")
    assert "does not work out profit" in outcome.caution.lower()


# --- crop claims ---------------------------------------------------------------------------------
def test_every_crop_claim_is_either_sourced_or_marked_research_needed():
    for claim in r.CROP_CLAIMS:
        assert claim.status in r.CLAIM_STATUSES
        if claim.status == "sourced":
            assert claim.source
            assert claim.evidence_type in r.EVIDENCE_TYPES
        else:
            assert claim.source is None
            assert claim.evidence_type is None
        assert claim.note


def test_unsourced_claims_say_what_kind_of_source_is_needed():
    for claim in r.CROP_CLAIMS:
        if claim.status == "research_needed":
            assert "citable source" in claim.note


def test_claim_ids_are_unique():
    ids = [claim.claim_id for claim in r.CROP_CLAIMS]
    assert len(ids) == len(set(ids))


def test_the_only_sourced_claim_is_the_one_marsden_supports():
    sourced = [claim for claim in r.CROP_CLAIMS if claim.status == "sourced"]
    assert [claim.claim_id for claim in sourced] == ["marsden_manure_to_diversified"]


# --- applicability rules -------------------------------------------------------------------------
def test_every_rule_is_structurally_valid():
    for rule in r.APPLICABILITY_RULES:
        assert rule.outcome_id in r.RULE_TARGETS
        assert rule.operator in r.OPERATORS
        assert rule.effect in r.RULE_EFFECTS
        assert rule.condition_text
        assert rule.rationale
        assert rule.evidence_basis in ("experimental_context", "team_proposed")
        assert rule.review in r.REVIEW_STATUSES


def test_no_rule_claims_to_be_expert_reviewed():
    assert all(rule.review == "not_expert_reviewed" for rule in r.APPLICABILITY_RULES)


def test_rule_ids_are_unique():
    ids = [rule.rule_id for rule in r.APPLICABILITY_RULES]
    assert len(ids) == len(set(ids))


def test_unknown_conditions_carry_no_value():
    for rule in r.APPLICABILITY_RULES:
        if rule.operator == "is_unknown":
            assert rule.value is None


def test_manure_rules_do_not_touch_the_herbicide_outcome():
    # PRD 7.6: no manure access limits the nitrogen comparison, not the herbicide comparison.
    manure_rules = [rule for rule in r.APPLICABILITY_RULES if rule.context_key == "manure_access"]
    assert manure_rules
    for rule in manure_rules:
        assert rule.outcome_id == "applied_n_reduction"
        assert rule.outcome_id != "herbicide_reduction"


def test_no_rule_applies_to_a_forbidden_outcome():
    forbidden = {"soil_carbon_change", "erosion_reduction", "nitrate_leaching_reduction"}
    assert not [rule for rule in r.APPLICABILITY_RULES if rule.outcome_id in forbidden]


def test_missing_data_abstains_rather_than_being_read_as_favourable():
    # PRD 8.5: missing data is never evidence of no risk or no benefit.
    for rule in r.APPLICABILITY_RULES:
        if rule.operator == "is_unknown" or rule.context_key == "required_indicators_all_known":
            assert rule.effect in ("abstain_outcome", "qualified")
            assert rule.effect != "in_domain"


def test_no_rule_rests_on_an_unsourced_claim():
    # Two rules that did (alfalfa drainage, oat season length) were withdrawn on 2026-11-15 rather than
    # applied unsourced. Nothing may quietly take their place.
    unsourced = {claim.claim_id for claim in r.CROP_CLAIMS if claim.status == "research_needed"}
    for rule in r.APPLICABILITY_RULES:
        named = [claim_id for claim_id in unsourced if claim_id in rule.rationale]
        assert not named, f"{rule.rule_id} rests on {named}"


def test_the_withdrawn_rules_are_gone():
    ids = {rule.rule_id for rule in r.APPLICABILITY_RULES}
    assert "applicability_alfalfa_drainage" not in ids
    assert "applicability_oat_season_length" not in ids


def test_the_claims_behind_the_withdrawn_rules_remain_open_questions():
    # Withdrawing the rules does not make the agronomy known; the questions stay on the record.
    by_id = {claim.claim_id: claim for claim in r.CROP_CLAIMS}
    for claim_id in ("alfalfa_drainage_sensitivity", "oat_season_window"):
        assert by_id[claim_id].status == "research_needed"
        assert "withdrawn" in by_id[claim_id].note


def test_the_weakest_rule_admits_it():
    rule = next(
        rule for rule in r.APPLICABILITY_RULES if rule.rule_id == "applicability_climate_distance_gdd"
    )
    assert rule.effect == "qualified"
    assert "no published basis" in rule.rationale


def test_operational_rules_cite_the_feasibility_requirement():
    operational = [
        rule
        for rule in r.APPLICABILITY_RULES
        if rule.outcome_id in r.STRATEGY_FEASIBILITY_TARGETS
    ]
    assert len(operational) >= 4
    for rule in operational:
        assert rule.effect in ("qualified", "out_of_domain")


def test_only_the_forage_outlet_rule_removes_an_option_on_operational_grounds():
    removed = [
        rule.rule_id
        for rule in r.APPLICABILITY_RULES
        if rule.outcome_id in r.STRATEGY_FEASIBILITY_TARGETS and rule.effect == "out_of_domain"
    ]
    assert removed == ["applicability_forage_outlet_strategy_c"]


# --- vocabularies --------------------------------------------------------------------------------
def test_decision_outcomes_are_exactly_the_three_the_prd_permits():
    assert r.DECISION_OUTCOMES == (
        "strategy_worth_exploring",
        "qualified_comparison",
        "abstention",
    )


def test_evidence_types_match_the_mission_label_set():
    assert set(r.EVIDENCE_TYPES) == {
        "observed",
        "derived",
        "classified",
        "survey",
        "model_reanalysis",
        "experimental",
        "published",
        "assumption",
    }


def test_rule_targets_cover_every_outcome_plus_the_comparison_wide_targets():
    for outcome in r.OUTCOME_EVIDENCE:
        assert outcome.outcome_id in r.RULE_TARGETS
    assert r.WHOLE_COMPARISON_TARGET in r.RULE_TARGETS
    assert set(r.STRATEGY_FEASIBILITY_TARGETS) <= set(r.RULE_TARGETS)


# --- the generated document ----------------------------------------------------------------------
def test_the_committed_document_matches_the_table():
    assert r.DOCUMENT_PATH.exists(), "run: python -m engine.rules.strategy_rules"
    committed = r.DOCUMENT_PATH.read_text(encoding="utf-8")
    assert committed == r.render_markdown(), (
        "docs/rules/strategy-profiles-and-applicability.md is stale; "
        "regenerate with: python -m engine.rules.strategy_rules"
    )


def test_the_document_leads_with_the_review_status():
    rendered = r.render_markdown()
    assert "NOT EXPERT-REVIEWED" in rendered.split("## 1.")[0]
    assert r.RULES_VERSION in rendered


def test_the_document_lists_every_rule_and_claim():
    rendered = r.render_markdown()
    for rule in r.APPLICABILITY_RULES:
        assert rule.rule_id in rendered
    for claim in r.CROP_CLAIMS:
        assert claim.claim_id in rendered
    for outcome in r.OUTCOME_EVIDENCE:
        assert outcome.outcome_id in rendered


def test_the_document_states_its_own_weaknesses():
    rendered = r.render_markdown()
    weaknesses = rendered.split("## 6. Known weaknesses")[1]
    assert "No rule has been reviewed by an agricultural expert" in weaknesses
    assert "were withdrawn on 2026-11-15" in weaknesses


def test_rendering_is_deterministic():
    assert r.render_markdown() == r.render_markdown()


def test_write_document_round_trips(tmp_path):
    target = tmp_path / "nested" / "rules.md"
    written = r.write_document(target)
    assert written == target
    assert target.read_text(encoding="utf-8") == r.render_markdown()


@pytest.mark.parametrize("profile", r.STRATEGY_PROFILES, ids=lambda p: p.strategy_id)
def test_each_profile_reaches_the_document(profile):
    rendered = r.render_markdown()
    assert profile.rotation in rendered
    for requirement in profile.operational_requirements:
        assert requirement in rendered


# --- what the farmer actually reads --------------------------------------------------------------
# The frontend shows `caution` as a plain sentence and `caution_reference` as a small source line, so
# internal shorthand must not appear in the caution itself.
INTERNAL_TERMS = ("PRD", "FR-", "NFR-", "research_needed", "claimable", "out_of_domain", "Table S", "Text S")


def test_no_caution_shown_to_a_farmer_contains_internal_shorthand():
    for outcome in r.OUTCOME_EVIDENCE:
        found = [term for term in INTERNAL_TERMS if term in outcome.caution]
        assert not found, f"{outcome.outcome_id} caution contains {found}"


def test_no_statement_shown_to_a_farmer_contains_internal_shorthand():
    for outcome in r.OUTCOME_EVIDENCE:
        found = [term for term in INTERNAL_TERMS if term in outcome.statement]
        assert not found, f"{outcome.outcome_id} statement contains {found}"


def test_the_code_word_research_needed_never_reaches_the_screen():
    for outcome in r.OUTCOME_EVIDENCE:
        assert "research_needed" not in outcome.caution
        assert "research_needed" not in outcome.caution_reference
    forage = next(o for o in r.OUTCOME_EVIDENCE if o.outcome_id == "forage_supply")
    assert "no source found yet" in forage.caution


def test_a_reference_is_a_short_source_line_not_a_sentence():
    for outcome in r.OUTCOME_EVIDENCE:
        assert len(outcome.caution_reference) <= 60, outcome.outcome_id
        assert not outcome.caution_reference.endswith(".")
