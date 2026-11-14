"""Tests for the Marsden reproduction (roadmap Phase 6 exit check).

Run from the repository root:  python -m pytest transform/marsden -q
"""
import hashlib

import pandas as pd
import pytest

from transform.marsden import marsden_repro as m


@pytest.fixture(scope="module")
def result(tmp_path_factory):
    return m.run(out=tmp_path_factory.mktemp("out"))


@pytest.fixture(scope="module")
def summary(result):
    return result["summary"].set_index("rotation")


# --- the Phase 6 exit check: PRD targets, computed from the raw records ---------------------
@pytest.mark.parametrize("rotation,total_n,herbicide", [
    ("2-yr", 74.5, 1.925),
    ("3-yr", 56.6, 0.261),
    ("4-yr", 40.8, 0.195),
])
def test_prd_targets(summary, rotation, total_n, herbicide):
    assert summary.loc[rotation, "applied_n"] == pytest.approx(total_n, abs=0.05)
    assert summary.loc[rotation, "herbicide"] == pytest.approx(herbicide, abs=0.0005)


def test_manufactured_and_manure_split(summary):
    assert summary.loc["3-yr", "manufactured_n"] == pytest.approx(16.7, abs=0.05)
    assert summary.loc["3-yr", "manure_n"] == pytest.approx(39.9, abs=0.05)
    assert summary.loc["4-yr", "manufactured_n"] == pytest.approx(10.9, abs=0.05)
    assert summary.loc["4-yr", "manure_n"] == pytest.approx(29.9, abs=0.05)
    assert summary.loc["2-yr", "manure_n"] == 0.0


def test_nine_seasons_per_rotation(summary):
    assert (summary["n_years"] == 9).all()


# --- reconciliation against the paper's own text --------------------------------------------
def _check(result, quantity, rotation, source="Davis 2012 Results text"):
    return next(c for c in result["checks"]
                if c.quantity == quantity and c.rotation == rotation and c.source == source)


@pytest.mark.parametrize("rotation", ["2-yr", "3-yr", "4-yr"])
def test_herbicide_matches_paper_text(result, rotation):
    assert _check(result, "herbicide", rotation).status == "MATCH"


def test_herbicide_reduction_is_88_percent(result):
    assert _check(result, "herbicide_reduction_pct", "3-yr & 4-yr").status == "MATCH"


@pytest.mark.parametrize("rotation", ["3-yr", "4-yr"])
def test_manufactured_n_diversified_consistent_with_paper(result, rotation):
    assert _check(result, "manufactured_n", rotation).status in {"MATCH", "WITHIN_SEM"}


@pytest.mark.xfail(strict=True, reason=(
    "Known, documented gap: the paper reports 80 +/- 3 kg N/ha/yr for the 2-yr system; Table S3 gives 74.5. "
    "The difference is isolated to 2011 (see test below). strict=True forces this note to be revisited if "
    "the gap ever closes."))
def test_manufactured_n_2yr_matches_paper_text(result):
    assert _check(result, "manufactured_n", "2-yr").status in {"MATCH", "WITHIN_SEM"}


def test_2yr_gap_is_isolated_to_2011(result):
    """Reading 2011 as the maize phase alone (not area-weighted) gives the paper's 80 +/- 3."""
    diag = next(c for c in result["checks"] if c.status == "INFO")
    assert abs(diag.computed - 80.0) <= 3.0
    by_year = result["by_year"]
    two = by_year[by_year["rotation"] == "2-yr"].set_index("year")["manufactured_n"]
    assert two.loc[2011] == pytest.approx(56.0)  # Table S3: maize 112, soybean 0
    assert two.drop(2011).mean() == pytest.approx((74.5 * 9 - 56.0) / 8)


# --- hand-computed golden case (equal-area weighting) ---------------------------------------
def test_equal_area_weighting_by_hand():
    fert = pd.DataFrame([
        # 2-yr, one year: (100 + 2) / 2 = 51 manufactured N
        dict(year=2003, rotation="2-yr", phase="maize", manufactured_n=100.0, manure_n=0.0),
        dict(year=2003, rotation="2-yr", phase="soybean", manufactured_n=2.0, manure_n=0.0),
        # 3-yr: manufactured (90 + 0 + 30) / 3 = 40; manure (120 + 0 + 0) / 3 = 40
        dict(year=2003, rotation="3-yr", phase="maize", manufactured_n=90.0, manure_n=120.0),
        dict(year=2003, rotation="3-yr", phase="soybean", manufactured_n=0.0, manure_n=0.0),
        dict(year=2003, rotation="3-yr", phase="small_grain_red_clover", manufactured_n=30.0, manure_n=0.0),
    ])
    herb = pd.DataFrame([
        dict(year=2003, crop="Maize", rotation="2-yr", active_ingredient="a", kg_ai_ha=1.5),
        dict(year=2003, crop="Maize", rotation="2-yr", active_ingredient="b", kg_ai_ha=0.5),
        dict(year=2003, crop="Soybean", rotation="2-yr", active_ingredient="c", kg_ai_ha=1.0),
        dict(year=2003, crop="Maize", rotation="3-yr", active_ingredient="a", kg_ai_ha=0.3),
        dict(year=2003, crop="Soybean", rotation="3-yr", active_ingredient="c", kg_ai_ha=0.6),
    ])
    out = m.rotation_year_inputs(fert, herb).set_index("rotation")
    assert out.loc["2-yr", "manufactured_n"] == pytest.approx(51.0)
    assert out.loc["2-yr", "herbicide"] == pytest.approx(1.5)      # (2.0 + 1.0) / 2
    assert out.loc["3-yr", "manufactured_n"] == pytest.approx(40.0)
    assert out.loc["3-yr", "manure_n"] == pytest.approx(40.0)
    assert out.loc["3-yr", "applied_n"] == pytest.approx(80.0)
    assert out.loc["3-yr", "herbicide"] == pytest.approx(0.3)      # (0.3 + 0.6 + 0) / 3


# --- integrity checks fail loudly -----------------------------------------------------------
@pytest.fixture
def raw_frames():
    fert = m.load_fertilizer(m.DEFAULT_RAW / m.FERTILIZER_FILE)
    herb = m.load_herbicide(m.DEFAULT_RAW / m.HERBICIDE_FILE)
    return fert, herb


def test_real_tables_are_complete(raw_frames):
    fert, herb = raw_frames
    assert len(fert) == 9 * (2 + 3 + 4)  # nine years x all phases of all three rotations
    m.validate_fertilizer(fert)
    m.validate_herbicide(herb)


def test_missing_fertilizer_row_is_rejected(raw_frames):
    fert, _ = raw_frames
    with pytest.raises(ValueError, match="missing"):
        m.validate_fertilizer(fert.iloc[1:])


def test_duplicate_fertilizer_row_is_rejected(raw_frames):
    fert, _ = raw_frames
    with pytest.raises(ValueError, match="duplicate"):
        m.validate_fertilizer(pd.concat([fert, fert.iloc[[0]]]))


def test_negative_rate_is_rejected(raw_frames):
    fert, _ = raw_frames
    bad = fert.copy()
    bad.loc[0, "manufactured_n"] = -1.0
    with pytest.raises(ValueError, match="negative"):
        m.validate_fertilizer(bad)


def test_missing_herbicide_year_is_not_treated_as_zero(raw_frames):
    _, herb = raw_frames
    bad = herb[~((herb["year"] == 2008) & (herb["rotation"] == "3-yr") & (herb["crop"] == "Soybean"))]
    with pytest.raises(ValueError, match="no record"):
        m.validate_herbicide(bad)


def test_unrecognised_phase_label_is_rejected():
    with pytest.raises(ValueError, match="unrecognised"):
        m._phase("Sorghum")


def test_footnote_symbols_are_stripped_from_active_ingredients(raw_frames):
    _, herb = raw_frames
    assert not herb["active_ingredient"].str.contains(r"[†‡§¶#*]").any()


# --- provenance and reproducibility ---------------------------------------------------------
def test_raw_files_match_manifest():
    assert m.verify_manifest(m.DEFAULT_RAW) == []


def test_tampered_input_is_detected(tmp_path):
    raw = tmp_path / "raw"
    raw.mkdir()
    for name in m.INPUT_FILES + ("MANIFEST.json",):
        (raw / name).write_bytes((m.DEFAULT_RAW / name).read_bytes())
    (raw / m.FERTILIZER_FILE).write_bytes(b"tampered")
    assert any("checksum mismatch" in p for p in m.verify_manifest(raw))
    with pytest.raises(RuntimeError, match="manifest"):
        m.run(raw, tmp_path / "out")


def test_rerun_gives_identical_tables(tmp_path):
    def digest(out):
        return {n: hashlib.sha256((out / n).read_bytes()).hexdigest()
                for n in ("management_by_year.csv", "management_summary.csv",
                          "reconciliation.csv", "indicator_lineage.json")}
    m.run(out=tmp_path / "a")
    m.run(out=tmp_path / "b")
    assert digest(tmp_path / "a") == digest(tmp_path / "b")


def test_every_indicator_has_a_complete_lineage_row():
    required = {"indicator_id", "source", "source_url", "product_version", "variables", "formula", "unit",
                "spatial_scale", "temporal_window", "missing_data_rule", "limitation", "evidence_type"}
    assert len(m.LINEAGE) == 4
    for row in m.LINEAGE:
        assert required <= set(row) and all(row[k] for k in required)
        assert row["evidence_type"] == "experimental"
