"""Validating and loading DS2's Marsden reproduction: conversion, lineage mapping, checks, and the real numbers."""

import io
import json
from pathlib import Path

import pandas as pd
import pandera.errors
import pytest

from common.schemas import INDICATOR_LINEAGE, MARSDEN_MANAGEMENT, MARSDEN_RECONCILIATION
from transform import marsden_load as ml

SCHEMA_ERRORS = (pandera.errors.SchemaError, pandera.errors.SchemaErrors)
REAL = ml.OUT_DIR
HAVE_REAL = (REAL / "management_summary.csv").exists()


def test_the_synthetic_outputs_pass_ds2s_schemas_and_the_des_checks(marsden_outputs):
    assert ml.problems(marsden_outputs) == []


def test_the_long_table_has_every_cell_once_and_passes_its_schema(marsden_outputs):
    long = ml.to_long(marsden_outputs)
    MARSDEN_MANAGEMENT.validate(long)
    assert len(long) == 27 * 4 + 3 * 4
    by_year = long[long["n_years"] == 1].pivot(index=["rotation", "first_year"], columns="metric", values="value")
    original = marsden_outputs.by_year.set_index(["rotation", "year"])[list(ml.INDICATORS)]
    pd.testing.assert_frame_equal(by_year[list(ml.INDICATORS)].reset_index(drop=True), original.reset_index(drop=True), check_names=False)
    nine = long[long["n_years"] == 9].pivot(index="rotation", columns="metric", values="value")
    pd.testing.assert_frame_equal(
        nine[list(ml.INDICATORS)], marsden_outputs.summary.set_index("rotation")[list(ml.INDICATORS)], check_names=False
    )
    assert set(long["evidence_type"]) == {"experimental"} and set(long["source_id"]) == {ml.SOURCE_ID}


def test_every_long_row_carries_its_indicator_id_and_unit(marsden_outputs):
    long = ml.to_long(marsden_outputs)
    assert dict(zip(long["metric"], long["indicator_id"], strict=True)) == ml.INDICATORS
    assert set(long.loc[long.metric == "herbicide", "unit"]) == {"kg ai ha-1 yr-1"}
    assert set(long.loc[long.metric != "herbicide", "unit"]) == {"kg N ha-1 yr-1"}


@pytest.mark.parametrize("edit, why", [
    (lambda f: f.assign(rotation=["5-yr"] + list(f["rotation"][1:])), "unknown rotation"),
    (lambda f: f.assign(evidence_type="observed"), "wrong evidence type"),
    (lambda f: f.assign(value=f["value"].where(f["metric"] != "herbicide", 50.0)), "herbicide unit error"),
    (lambda f: f.assign(value=f["value"].where(f["metric"] != "manure_n", f["value"] * 100)), "nitrogen unit error"),
    (lambda f: f.assign(last_year=f["first_year"] - 1), "period runs backwards"),
    (lambda f: f.assign(n_years=3), "n_years does not match the period"),
    (lambda f: pd.concat([f, f.head(1)], ignore_index=True), "duplicate key"),
])
def test_the_long_schema_rejects_bad_frames(marsden_outputs, edit, why):
    with pytest.raises(SCHEMA_ERRORS):
        MARSDEN_MANAGEMENT.validate(edit(ml.to_long(marsden_outputs)))


def test_applied_n_must_equal_manufactured_plus_manure(marsden_outputs):
    long = ml.to_long(marsden_outputs)
    broken = long.copy()
    broken.loc[(broken.metric == "applied_n") & (broken.index == broken.index[broken.metric == "applied_n"][0]), "value"] += 5
    with pytest.raises(SCHEMA_ERRORS):
        MARSDEN_MANAGEMENT.validate(broken)


def test_lineage_mapping_follows_the_runner_convention_and_fits_the_table(marsden_outputs):
    frame = ml.lineage_frame(marsden_outputs)
    INDICATOR_LINEAGE.validate(frame)
    assert list(frame.columns) == ml.LINEAGE_COLUMNS and len(frame) == 4
    row = frame.iloc[0]
    assert row["label"] == row["indicator_id"].replace("_", " ") and row["scale"] == "site"
    assert row["interpretation"] == row["formula"] and row["resolution"] == row["spatial_support"]
    assert row["aggregation_window"] == "annual, 2003-2011 (9 seasons)"
    assert json.loads(row["source_ids"]) == ["Marsden Farm supplementary data, Davis et al. (2012) PLOS ONE"]
    assert json.loads(row["variables"]) == [marsden_outputs.lineage[0]["variables"]]  # her string, as a one-item list
    assert row["code_version"] == "marsden_repro@2f2eb2dfd218" and row["run_id"] == "ds2-marsden-20261115T054836Z"


def test_the_unreconciled_check_and_the_note_are_carried_unchanged(marsden_outputs):
    frame = ml.reconciliation_frame(marsden_outputs)
    MARSDEN_RECONCILIATION.validate(frame)
    assert frame["status"].tolist() == marsden_outputs.reconciliation["status"].tolist()  # nothing re-labelled
    gap = frame[frame["status"] == "UNRECONCILED"]
    assert len(gap) == 1 and gap.iloc[0]["note"] == "Table S3 gives 74.5, the text gives 80"
    with pytest.raises(SCHEMA_ERRORS):
        MARSDEN_RECONCILIATION.validate(frame.assign(status="FIXED"))


def test_problems_names_a_missing_lineage_row_wrong_counts_and_missing_years(marsden_outputs):
    marsden_outputs.lineage = marsden_outputs.lineage[:3]
    found = ml.problems(marsden_outputs)
    assert any("lineage: 3 rows, expected 4" in p for p in found)
    assert any("marsden_herbicide_kg_ai_ha_yr" in p for p in found)
    marsden_outputs.by_year = marsden_outputs.by_year[marsden_outputs.by_year["year"] != 2007]
    assert any("by-year rows cover" in p for p in ml.problems(marsden_outputs))


def test_ds2s_own_schema_findings_are_passed_through(marsden_outputs):
    marsden_outputs.by_year.loc[0, "applied_n"] += 10
    assert any("applied_n" in p for p in ml.problems(marsden_outputs))


class FakeS3:
    def __init__(self, shas):
        self.shas = shas

    def get_object(self, Bucket, Key):
        name = Key.removeprefix(f"{ml.RAW_PREFIX}/").removesuffix(".manifest.json")
        return {"Body": io.BytesIO(json.dumps({"sha256": self.shas[name]}).encode())}


def test_input_checksums_must_equal_the_s3_manifests(marsden_outputs):
    same = FakeS3(dict(marsden_outputs.run_manifest["inputs"]))
    assert ml.checksum_problems(marsden_outputs.run_manifest, same, "b") == []
    other = FakeS3({**marsden_outputs.run_manifest["inputs"], "pone.0047149.s004.docx": "c" * 64})
    found = ml.checksum_problems(marsden_outputs.run_manifest, other, "b")
    assert len(found) == 1 and "pone.0047149.s004.docx" in found[0]


def write_outputs(folder: Path, outputs):
    folder.mkdir(parents=True, exist_ok=True)
    outputs.by_year.to_csv(folder / "management_by_year.csv", index=False)
    outputs.summary.to_csv(folder / "management_summary.csv", index=False)
    outputs.reconciliation.to_csv(folder / "reconciliation.csv", index=False)
    (folder / "indicator_lineage.json").write_text(json.dumps(outputs.lineage))
    (folder / "run_manifest.json").write_text(json.dumps(outputs.run_manifest))


def test_a_blank_reconciliation_note_is_read_as_text_not_nan(tmp_path, marsden_outputs):
    write_outputs(tmp_path, marsden_outputs)
    read = ml.read_outputs(tmp_path)
    assert read.reconciliation["note"].map(type).eq(str).all() and (read.reconciliation["note"] == "").sum() == 19


def test_main_dry_run_loads_nothing_and_a_bad_set_is_refused_before_the_database(tmp_path, marsden_outputs, monkeypatch, capsys):
    monkeypatch.setattr(ml, "load_all", lambda *a: pytest.fail("the database must not be touched"))
    write_outputs(tmp_path, marsden_outputs)
    assert ml.main(["--out", str(tmp_path)]) == 0
    assert "dry run" in capsys.readouterr().out
    marsden_outputs.lineage = marsden_outputs.lineage[:2]
    write_outputs(tmp_path, marsden_outputs)
    assert ml.main(["--out", str(tmp_path), "--load"]) == 1
    assert "REFUSED" in capsys.readouterr().out


def test_a_missing_output_folder_is_reported_cleanly(tmp_path, capsys):
    assert ml.main(["--out", str(tmp_path / "nowhere")]) == 1
    assert "marsden:" in capsys.readouterr().out


PRD_APPLIED_N = {"2-yr": 74.5, "3-yr": 56.6, "4-yr": 40.8}
PRD_HERBICIDE = {"2-yr": 1.925, "3-yr": 0.261, "4-yr": 0.195}


@pytest.mark.skipif(not HAVE_REAL, reason="DS2's outputs are not here (run python -m transform.marsden.marsden_repro)")
def test_the_real_outputs_validate_and_hit_the_prd_targets():
    outputs = ml.read_outputs(REAL)
    assert ml.problems(outputs) == []
    nine = outputs.summary.set_index("rotation")
    for rotation, target in PRD_APPLIED_N.items():  # her rule: within half of the last printed digit
        assert abs(nine.loc[rotation, "applied_n"] - target) <= 0.05
        assert abs(nine.loc[rotation, "herbicide"] - PRD_HERBICIDE[rotation]) <= 0.0005
    long = ml.to_long(outputs)
    MARSDEN_MANAGEMENT.validate(long)
    INDICATOR_LINEAGE.validate(ml.lineage_frame(outputs))
    MARSDEN_RECONCILIATION.validate(ml.reconciliation_frame(outputs))
    assert len(long) == 120


@pytest.mark.skipif(not HAVE_REAL, reason="DS2's outputs are not here (run python -m transform.marsden.marsden_repro)")
def test_the_real_reconciliation_keeps_its_one_gap_visible():
    rec = ml.read_outputs(REAL).reconciliation
    prd = rec[rec["source"].str.startswith("PRD")]
    assert len(prd) == 12 and (prd["status"] == "MATCH").all()
    gap = rec[rec["status"] == "UNRECONCILED"]
    assert len(gap) == 1 and (gap.iloc[0]["quantity"], gap.iloc[0]["rotation"]) == ("manufactured_n", "2-yr")
    assert gap.iloc[0]["computed"] == pytest.approx(74.5) and gap.iloc[0]["reference"] == pytest.approx(80.0)
