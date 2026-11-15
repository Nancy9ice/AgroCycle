"""Tests for priority-driven emphasis (roadmap Phase 10; review section 5.1).

The property that matters: priorities change the order and the gaps called out, and nothing else. If one of
these ever fails by returning a different outcome or a shorter list, the module has become a scoring system,
which PRD 8.5 forbids.

Run from the repository root:  uv run pytest engine/tests/test_emphasis.py -q
"""
import pytest

from engine import decision as d
from engine import emphasis as e

ALL_OK = dict.fromkeys(d.REQUIRED_INDICATORS, "ok")


def decision() -> d.Decision:
    profile = d.FieldProfile(
        field_id="primary-001",
        boundary_source="demo",
        crop_history_summary="maize-soybean 2015-2025",
        county="Story",
        crop_history_is_maize_soybean=True,
        frost_free_days=168,
        dominant_drainage_class="Poorly drained",
        indicator_statuses=ALL_OK,
    )
    return d.assess(profile, d.FarmerConstraints(True, True, True, True))


# --- it must not become a scoring system ---------------------------------------------------------
def test_priorities_never_change_the_outcome():
    base = decision()
    for priorities in ({}, {"soil": "high"}, {"income": "high", "water": "high"}):
        shaped = e.emphasise(base, priorities)
        assert shaped.outcome == base.outcome
        assert shaped.outcome_reason == base.outcome_reason


def test_every_outcome_is_still_returned():
    base = decision()
    shaped = e.emphasise(base, {"forage": "high"})
    assert len(shaped.outcomes) == len(base.outcomes)
    assert {o.outcome_id for o in shaped.outcomes} == {o.outcome_id for o in base.outcomes}


def test_nothing_is_hidden_because_the_farmer_did_not_ask():
    # A farmer who cares only about income still sees the herbicide and soil entries.
    shaped = e.emphasise(decision(), {"income": "high"})
    ids = {o.outcome_id for o in shaped.outcomes}
    assert "herbicide_reduction" in ids
    assert "soil_carbon_change" in ids


def test_no_strategy_is_ranked_or_scored():
    shaped = e.emphasise(decision(), {"soil": "high"})
    fields = set(vars(shaped))
    for forbidden in ("score", "rank", "ranking", "winner", "best", "weight", "strategies"):
        assert not any(forbidden in name for name in fields)


# --- it must actually reorder ---------------------------------------------------------------------
def test_a_soil_priority_puts_the_soil_evidence_first():
    shaped = e.emphasise(decision(), {"soil": "high"})
    assert shaped.outcomes[0].outcome_id in e.PRIORITY_OUTCOMES["soil"]
    assert shaped.highlighted[0] == "soil_carbon_change"


def test_an_input_priority_leads_with_nitrogen_and_herbicide():
    shaped = e.emphasise(decision(), {"inputs": "high"})
    assert [o.outcome_id for o in shaped.outcomes[:2]] == [
        "applied_n_reduction",
        "herbicide_reduction",
    ]


def test_two_priorities_keep_the_order_they_were_given():
    shaped = e.emphasise(decision(), {"inputs": "high", "income": "high"})
    assert shaped.highlighted[0] == "applied_n_reduction"
    assert "profitability_parity" in shaped.highlighted
    assert shaped.highlighted.index("applied_n_reduction") < shaped.highlighted.index(
        "profitability_parity"
    )


def test_an_outcome_serving_two_priorities_appears_once():
    shaped = e.emphasise(decision(), {"soil": "high", "inputs": "high"})
    assert shaped.highlighted.count("applied_n_reduction") == 1


def test_no_priorities_means_the_engine_order_is_kept():
    base = decision()
    shaped = e.emphasise(base, None)
    assert [o.outcome_id for o in shaped.outcomes] == [o.outcome_id for o in base.outcomes]
    assert shaped.highlighted == ()
    assert shaped.gaps_for_priorities == ()


def test_a_low_priority_promotes_nothing():
    # "low" is an answer, not silence, and neither promotes anything.
    shaped = e.emphasise(decision(), {"soil": "low"})
    assert shaped.highlighted == ()
    assert shaped.priorities_used == ()


def test_an_unknown_priority_key_is_ignored():
    shaped = e.emphasise(decision(), {"something_else": "high"})
    assert shaped.priorities_used == ()


# --- the gaps are the honest half -----------------------------------------------------------------
def test_each_chosen_priority_brings_its_own_gap():
    shaped = e.emphasise(decision(), {"soil": "high", "income": "medium"})
    assert len(shaped.gaps_for_priorities) == 2
    joined = " ".join(shaped.gaps_for_priorities)
    assert "soil carbon" in joined
    assert "does not work out profit" in joined


def test_a_forage_priority_says_we_have_no_forage_figures():
    shaped = e.emphasise(decision(), {"forage": "high"})
    assert "no figures for forage yield" in shaped.gaps_for_priorities[0]


@pytest.mark.parametrize("priority", sorted(e.PRIORITY_OUTCOMES))
def test_every_priority_has_a_gap_and_maps_to_real_outcomes(priority):
    assert priority in e.PRIORITY_GAPS
    assert e.PRIORITY_GAPS[priority].strip()
    known = {outcome.outcome_id for outcome in decision().outcomes}
    for outcome_id in e.PRIORITY_OUTCOMES[priority]:
        assert outcome_id in known, f"{priority} points at {outcome_id}, which no outcome provides"


def test_the_note_says_priorities_do_not_change_the_result():
    shaped = e.emphasise(decision(), {"soil": "high"})
    assert "do not change the result" in shaped.note
    assert "scored or ranked" in shaped.note
