"""Tests for the Marsden Pandera schemas (roadmap Phase 6, the validation half).

A schema that only ever passes proves nothing, so every check here breaks something deliberately and
asserts the schema catches it.

Run from the repository root:  uv run pytest transform/marsden -q
"""
import pandas as pd
import pytest

from transform.marsden import marsden_repro as m
from transform.marsden import schemas as s


@pytest.fixture(scope="module")
def outputs(tmp_path_factory):
    result = m.run(out=tmp_path_factory.mktemp("out"))
    reconciliation = pd.DataFrame([vars(check) for check in result["checks"]]).round(6)
    return result["by_year"], result["summary"], reconciliation


# --- the real outputs pass -----------------------------------------------------------------------
def test_the_real_outputs_validate(outputs):
    by_year, summary, reconciliation = outputs
    assert s.validate_outputs(by_year, summary, reconciliation, m.LINEAGE) == []


def test_the_real_lineage_is_complete():
    assert s.lineage_findings(m.LINEAGE) == []
    assert len(m.LINEAGE) == 4


# --- by-year table -------------------------------------------------------------------------------
def test_an_unknown_rotation_is_rejected(outputs):
    by_year = outputs[0].copy()
    by_year.loc[0, "rotation"] = "5-yr"
    findings = s.validate_outputs(by_year, outputs[1])
    assert any("rotation" in finding for finding in findings)


def test_a_year_outside_the_experiment_is_rejected(outputs):
    by_year = outputs[0].copy()
    by_year.loc[0, "year"] = 1999
    assert s.validate_outputs(by_year, outputs[1])


def test_negative_nitrogen_is_rejected(outputs):
    by_year = outputs[0].copy()
    by_year.loc[0, "manufactured_n"] = -1.0
    assert s.validate_outputs(by_year, outputs[1])


def test_a_unit_error_in_nitrogen_is_rejected(outputs):
    # kg/ha mistaken for g/ha would land far above any plausible rate.
    by_year = outputs[0].copy()
    by_year.loc[0, "manufactured_n"] = 74_500.0
    assert s.validate_outputs(by_year, outputs[1])


def test_applied_n_that_does_not_match_its_components_is_rejected(outputs):
    by_year = outputs[0].copy()
    by_year.loc[0, "applied_n"] = by_year.loc[0, "applied_n"] + 5.0
    findings = s.validate_outputs(by_year, outputs[1])
    assert any("applied_n" in finding or "table" in finding for finding in findings)


def test_a_duplicate_rotation_year_is_rejected(outputs):
    by_year = pd.concat([outputs[0], outputs[0].iloc[[0]]], ignore_index=True)
    assert s.validate_outputs(by_year, outputs[1])


def test_a_dropped_season_is_rejected(outputs):
    by_year = outputs[0].iloc[1:].reset_index(drop=True)
    assert s.validate_outputs(by_year, outputs[1])


def test_a_missing_column_is_reported_by_name(outputs):
    by_year = outputs[0].drop(columns=["herbicide"])
    findings = s.validate_outputs(by_year, outputs[1])
    assert any("missing column(s) herbicide" in finding for finding in findings)


# --- summary table -------------------------------------------------------------------------------
def test_a_summary_with_the_wrong_season_count_is_rejected(outputs):
    summary = outputs[1].copy()
    summary.loc[0, "n_years"] = 8
    assert s.validate_outputs(outputs[0], summary)


def test_a_summary_missing_a_rotation_is_rejected(outputs):
    summary = outputs[1].iloc[:2].reset_index(drop=True)
    assert s.validate_outputs(outputs[0], summary)


def test_a_repeated_rotation_in_the_summary_is_rejected(outputs):
    summary = pd.concat([outputs[1], outputs[1].iloc[[0]]], ignore_index=True)
    assert s.validate_outputs(outputs[0], summary)


# --- reconciliation ------------------------------------------------------------------------------
def test_an_unknown_reconciliation_status_is_rejected(outputs):
    reconciliation = outputs[2].copy()
    reconciliation.loc[0, "status"] = "PROBABLY_FINE"
    assert s.validate_outputs(outputs[0], outputs[1], reconciliation)


def test_a_reconciliation_row_without_a_source_is_rejected(outputs):
    reconciliation = outputs[2].copy()
    reconciliation.loc[0, "source"] = ""
    assert s.validate_outputs(outputs[0], outputs[1], reconciliation)


# --- lineage -------------------------------------------------------------------------------------
def test_lineage_with_an_empty_field_is_rejected():
    rows = [dict(row) for row in m.LINEAGE]
    rows[0]["limitation"] = ""
    findings = s.lineage_findings(rows)
    assert any("empty field(s) limitation" in finding for finding in findings)


def test_lineage_with_an_invented_evidence_type_is_rejected():
    rows = [dict(row) for row in m.LINEAGE]
    rows[0]["evidence_type"] = "probably_true"
    assert any("not a label" in finding for finding in s.lineage_findings(rows))


def test_duplicate_lineage_ids_are_rejected():
    rows = [dict(row) for row in m.LINEAGE]
    assert any("duplicate" in finding for finding in s.lineage_findings(rows + [rows[0]]))


def test_empty_lineage_is_rejected():
    assert s.lineage_findings([]) == ["lineage: no rows"]


# --- the pipeline stops on a bad table -------------------------------------------------------------
def test_run_refuses_to_write_an_invalid_table(tmp_path, monkeypatch):
    original = m.nine_year_means

    def wrong_means(by_year):
        summary = original(by_year)
        summary.loc[0, "applied_n"] = summary.loc[0, "applied_n"] + 10.0
        return summary

    monkeypatch.setattr(m, "nine_year_means", wrong_means)
    with pytest.raises(RuntimeError, match="failed schema validation"):
        m.run(out=tmp_path)
    assert not (tmp_path / "management_summary.csv").exists()
