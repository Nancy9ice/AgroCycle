"""Tests for the season stress summary (F2) and the transition sequence (F6).

Both exist because the features BE asked for could not be sourced. The tests guard the line: these tables
may carry what the experiment establishes and what our own indicators measure, and must not quietly acquire
a crop-phase window, a stage-specific threshold or a sowing date.

Run from the repository root:  uv run pytest engine/tests/test_stress_and_transition.py -q
"""
import pytest

from engine import season_stress as f2
from engine import transition as f6
from engine.rules import strategy_rules as rules
from transform.indicators import climate

# Words that would mean we had started inventing agronomy.
CROP_STAGE_WORDS = ("silking", "pod fill", "tasselling", "anthesis", "emergence", "flowering")
MONTHS = (
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "November", "December",
)


# --- F2: the season stress summary ----------------------------------------------------------------
def test_every_column_comes_from_an_indicator_that_exists():
    known = {record["indicator_id"] for record in climate.INDICATOR_LINEAGE}
    for indicator_id in f2.COLUMNS:
        assert indicator_id in known, f"{indicator_id} has no lineage record"


def test_every_column_has_a_threshold_row():
    documented = {row["column"] for row in f2.THRESHOLDS}
    assert documented == set(f2.COLUMNS.values())


def test_every_threshold_is_declared_team_proposed_and_unreviewed():
    for row in f2.threshold_rows("test"):
        assert row["evidence_basis"] == "team_proposed"
        assert row["review"] == "not_expert_reviewed"
        assert row["limitation"]


def test_the_thresholds_match_the_indicator_module():
    by_column = {row["column"]: row for row in f2.THRESHOLDS}
    assert f"{climate.HEAT_DAY_THRESHOLD_C:g}" in by_column["heat_days"]["threshold"]
    assert f"{climate.WET_DAY_THRESHOLD_MM:g}" in by_column["longest_dry_spell_days"]["threshold"]
    assert f"{climate.DRY_SPELL_MIN_DAYS}" in by_column["dry_spells"]["threshold"]
    assert f"{climate.GDD_BASE_C:g}" in by_column["growing_degree_days"]["threshold"]


def test_no_threshold_claims_to_be_about_a_crop_stage():
    for row in f2.THRESHOLDS:
        text = f"{row['what_it_counts']} {row['threshold']} {row['limitation']}".lower()
        for word in CROP_STAGE_WORDS:
            assert word not in text, f"{row['column']} mentions {word}"


def test_the_counting_columns_say_they_are_not_a_crop_stage():
    for column in ("heat_days", "longest_dry_spell_days", "dry_spells", "growing_degree_days"):
        row = next(r for r in f2.THRESHOLDS if r["column"] == column)
        assert "says nothing about which crop stage" in row["limitation"]


def test_the_rainfall_limitation_carries_the_measured_shortfall():
    row = next(r for r in f2.THRESHOLDS if r["column"] == "rainfall_mm")
    assert "11 %" in row["limitation"]


def test_the_view_reads_field_indicators_rather_than_copying_it():
    # A copy would drift from the indicators; a view cannot.
    assert "CREATE OR REPLACE VIEW" in f2.VIEW_DDL
    assert "FROM field_indicators" in f2.VIEW_DDL
    assert "INSERT" not in f2.VIEW_DDL.upper()


# --- F6: the transition sequence -------------------------------------------------------------------
def test_every_step_declares_a_known_evidence_basis():
    for step in f6.TRANSITION_STEPS:
        assert step.evidence_basis in f6.EVIDENCE_BASES
        assert step.source
        assert step.action


def test_nothing_in_the_table_is_an_assumption():
    # If a row ever needs `assumption`, it needs a decision first, not a quiet addition.
    assert not [s for s in f6.TRANSITION_STEPS if s.evidence_basis == "assumption"]


def test_only_the_manure_step_states_a_time_of_year():
    for step in f6.TRANSITION_STEPS:
        if step.crop == "manure":
            assert "October" in step.timing_note
            assert step.evidence_basis == "experimental"
            assert "Text S1" in step.timing_note or "Text S1" in step.source
            continue
        assert step.timing_note == f6.NOT_ESTABLISHED
        for month in MONTHS:
            assert month not in step.timing_note


def test_no_step_mentions_a_crop_stage():
    for step in f6.TRANSITION_STEPS:
        text = f"{step.action} {step.timing_note} {' '.join(step.needs)}".lower()
        for word in CROP_STAGE_WORDS:
            assert word not in text, f"{step.strategy_id} year {step.year} mentions {word}"


@pytest.mark.parametrize("strategy_id", ["B", "C"])
def test_the_sequence_matches_the_strategy_it_belongs_to(strategy_id):
    profile = next(p for p in rules.STRATEGY_PROFILES if p.strategy_id == strategy_id)
    years = sorted(s.year for s in f6.TRANSITION_STEPS if s.strategy_id == strategy_id and s.year)
    assert years == list(range(1, len(profile.phases) + 1))


def test_both_diversified_strategies_carry_the_manure_step():
    manure = {s.strategy_id for s in f6.TRANSITION_STEPS if s.crop == "manure"}
    assert manure == {"B", "C"}


def test_steps_derived_from_the_rotation_say_so_rather_than_claiming_a_source():
    derived = [s for s in f6.TRANSITION_STEPS if s.evidence_basis == "team_proposed"]
    assert derived
    for step in derived:
        assert "not from a source" in step.source


def test_every_step_that_needs_something_says_what():
    for step in f6.TRANSITION_STEPS:
        assert step.needs, f"{step.strategy_id} year {step.year} lists no needs"
