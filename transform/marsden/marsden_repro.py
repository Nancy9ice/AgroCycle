#!/usr/bin/env python3
"""Marsden Farm management reproduction (AgroCycle, DS2, roadmap Phase 6).

Rebuilds the rotation-level management summaries from the supplementary records of
Davis, Hill, Chase, Johanns & Liebman (2012), PLOS ONE 7(10): e47149:

  * Table S3 (pone.0047149.s004.docx): manufactured-fertilizer N and manure N by year/crop phase
  * Table S4 (pone.0047149.s005.docx): herbicide active ingredient by year/crop/rotation

Method (Text S1, "Economic analyses"): each land unit is divided into equal portions per
crop phase: 2 (2-yr), 3 (3-yr) and 4 (4-yr). The rotation-level value for a year is therefore the
sum over phases divided by the number of phases; the nine-year value is the mean of 2003-2011.
Phases with no herbicide application (small grain, forage legumes) contribute zero, as documented
in Text S1; Table S4 lists maize and soybean only.

Evidence type for every output: ``experimental`` (a derived summary of experimental records from
one research site; not a field-level prediction).

Usage (from the repository root):  python -m transform.marsden.marsden_repro [--raw DIR] [--out DIR] [--strict]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import re
import sys
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

import docx
import pandas as pd

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]
DEFAULT_RAW = REPO_ROOT / "data" / "raw" / "marsden" / "pone.0047149-supplement" / "2026-11-13"
DEFAULT_OUT = REPO_ROOT / "data" / "out" / "marsden"

ROTATIONS = ("2-yr", "3-yr", "4-yr")
YEARS = tuple(range(2003, 2012))  # nine growing seasons
PHASES = {
    "2-yr": ("maize", "soybean"),
    "3-yr": ("maize", "soybean", "small_grain_red_clover"),
    "4-yr": ("maize", "soybean", "small_grain_alfalfa", "alfalfa"),
}
N_PHASES = {r: len(p) for r, p in PHASES.items()}
HERBICIDE_CROPS = ("Maize", "Soybean")

FERTILIZER_FILE = "pone.0047149.s004.docx"
HERBICIDE_FILE = "pone.0047149.s005.docx"
INPUT_FILES = (
    "pone.0047149.pdf",
    "pone.0047149.s002.docx",
    FERTILIZER_FILE,
    HERBICIDE_FILE,
    "pone.0047149.s007.docx",
)

# --- reference values ---------------------------------------------------------------------
# PRD section 7.4 (team's reproduced values; the test targets in specs/roadmap.md Phase 6).
PRD_TARGETS = {
    ("manufactured_n", "2-yr"): 74.5, ("manufactured_n", "3-yr"): 16.7, ("manufactured_n", "4-yr"): 10.9,
    ("manure_n", "2-yr"): 0.0, ("manure_n", "3-yr"): 39.9, ("manure_n", "4-yr"): 29.9,
    ("applied_n", "2-yr"): 74.5, ("applied_n", "3-yr"): 56.6, ("applied_n", "4-yr"): 40.8,
    ("herbicide", "2-yr"): 1.925, ("herbicide", "3-yr"): 0.261, ("herbicide", "4-yr"): 0.195,
}
PRD_STEP = {"manufactured_n": 0.1, "manure_n": 0.1, "applied_n": 0.1, "herbicide": 0.001}

# Davis et al. 2012, Results, "Agrichemical, Labor and Energy Inputs": (mean, SEM, last-digit step).
PAPER_TEXT = {
    ("manufactured_n", "2-yr"): (80.0, 3.0, 1.0),
    ("manufactured_n", "3-yr"): (16.0, 3.0, 1.0),
    ("manufactured_n", "4-yr"): (11.0, 2.0, 1.0),
    ("herbicide", "2-yr"): (1.9, 0.06, 0.1),
    ("herbicide", "3-yr"): (0.26, 0.05, 0.01),
    ("herbicide", "4-yr"): (0.20, 0.03, 0.01),
}
PAPER_HERBICIDE_REDUCTION_PCT = 88.0  # "reducing herbicide use by 88% in the 3-yr and 4-yr rotations"

CITATION = "Davis et al. (2012) PLOS ONE 7(10): e47149, https://doi.org/10.1371/journal.pone.0047149"
SOURCE_URL = "https://pmc.ncbi.nlm.nih.gov/articles/PMC3468434/"

LINEAGE = [
    {
        "indicator_id": "marsden_manufactured_n_kg_ha_yr",
        "variables": "Table S3 manufactured-fertilizer N (kg N/ha) by year and crop phase",
        "formula": "mean over 2003-2011 of [sum over phases / number of phases] per rotation",
        "unit": "kg N ha-1 yr-1",
        "limitation": "Treatment-level table values, not plot-level records; one site.",
    },
    {
        "indicator_id": "marsden_manure_n_kg_ha_yr",
        "variables": "Table S3 manure N (kg N/ha) by year and crop phase",
        "formula": "same equal-area weighting as manufactured N",
        "unit": "kg N ha-1 yr-1",
        "limitation": "Total N in composted manure, not plant-available N. Table S3 lists manure on the maize "
                      "row although Text S1 says it was applied in October to clover/alfalfa; the average is "
                      "unaffected.",
    },
    {
        "indicator_id": "marsden_applied_n_kg_ha_yr",
        "variables": "manufactured N + manure N",
        "formula": "marsden_manufactured_n + marsden_manure_n",
        "unit": "kg N ha-1 yr-1",
        "limitation": "Applied N only. It excludes biological N fixation by red clover and alfalfa, so it is NOT "
                      "total N supply. The PRD label 'total N' should read 'applied N (manufactured + manure)'.",
    },
    {
        "indicator_id": "marsden_herbicide_kg_ai_ha_yr",
        "variables": "Table S4 herbicide active ingredient (kg ai/ha) for maize and soybean phases",
        "formula": "mean over 2003-2011 of [sum of all active ingredients / number of phases]; "
                   "phases without herbicide count as zero",
        "unit": "kg ai ha-1 yr-1",
        "limitation": "Mass of active ingredient says nothing about toxicity; insecticides (2007-2009) are "
                      "excluded; one site.",
    },
]
for _row in LINEAGE:
    _row.update({
        "source": f"Marsden Farm supplementary data, {CITATION}",
        "source_url": SOURCE_URL,
        "product_version": "PLOS ONE 7(10) supporting information, Oct 2012",
        "spatial_scale": "single experimental site (Marsden Farm, Boone Co., Iowa; 42.02 N, 93.78 W)",
        "temporal_window": "annual, 2003-2011 (9 seasons)",
        "missing_data_rule": "none permitted: the run aborts unless every year x rotation x phase is present",
        "evidence_type": "experimental",
    })


# --- loading ------------------------------------------------------------------------------
def _table_rows(path: Path) -> list[list[str]]:
    document = docx.Document(str(path))
    if len(document.tables) != 1:
        raise ValueError(f"{path.name}: expected exactly 1 table, found {len(document.tables)}")
    return [[cell.text.strip() for cell in row.cells] for row in document.tables[0].rows]


def _num(text: str, where: str) -> float:
    try:
        return float(text)
    except ValueError as exc:
        raise ValueError(f"non-numeric value {text!r} at {where}") from exc


def _phase(label: str) -> str:
    key = re.sub(r"\s+", "", label.lower())
    table = {
        "maize": "maize",
        "soybean": "soybean",
        "alfalfa": "alfalfa",
        "triticale/redclover": "small_grain_red_clover",
        "oat/redclover": "small_grain_red_clover",
        "triticale/alfalfa": "small_grain_alfalfa",
        "oat/alfalfa": "small_grain_alfalfa",
    }
    if key not in table:
        raise ValueError(f"unrecognised crop phase label {label!r}")
    return table[key]


def load_fertilizer(path: Path) -> pd.DataFrame:
    """Table S3 -> one row per (year, rotation, phase)."""
    records = []
    for row in _table_rows(path):
        if not row or not row[0].isdigit():
            continue  # header or footnote rows
        where = f"{path.name} year {row[0]} {row[1]} {row[2]}"
        records.append({
            "year": int(row[0]),
            "rotation": row[2],
            "phase": _phase(row[1]),
            "manufactured_n": _num(row[3], where),
            "manure_n": _num(row[6], where),
        })
    return pd.DataFrame.from_records(records)


def load_herbicide(path: Path) -> pd.DataFrame:
    """Table S4 -> one row per (year, crop, rotation, active ingredient)."""
    records = []
    for row in _table_rows(path):
        if not row or not row[0].isdigit():
            continue
        where = f"{path.name} year {row[0]} {row[1]} {row[2]} {row[3]}"
        records.append({
            "year": int(row[0]),
            "crop": row[1],
            "rotation": row[2],
            "active_ingredient": re.sub(r"[†‡§¶#*]+$", "", row[3]).strip(),
            "kg_ai_ha": _num(row[4], where),
        })
    return pd.DataFrame.from_records(records)


# --- integrity checks (fail loudly) -------------------------------------------------------
def validate_fertilizer(df: pd.DataFrame) -> None:
    expected = {(y, r, p) for y in YEARS for r in ROTATIONS for p in PHASES[r]}
    keys = list(zip(df["year"], df["rotation"], df["phase"]))
    if len(keys) != len(set(keys)):
        raise ValueError("fertilizer table: duplicate (year, rotation, phase) rows")
    missing, extra = expected - set(keys), set(keys) - expected
    if missing or extra:
        raise ValueError(f"fertilizer table: missing {sorted(missing)[:5]} extra {sorted(extra)[:5]}")
    if df[["manufactured_n", "manure_n"]].isna().any().any():
        raise ValueError("fertilizer table: null values")
    if (df[["manufactured_n", "manure_n"]] < 0).any().any():
        raise ValueError("fertilizer table: negative application rate")


def validate_herbicide(df: pd.DataFrame) -> None:
    if not set(df["rotation"]) <= set(ROTATIONS):
        raise ValueError(f"herbicide table: unexpected rotations {set(df['rotation']) - set(ROTATIONS)}")
    if not set(df["crop"]) <= set(HERBICIDE_CROPS):
        raise ValueError(f"herbicide table: unexpected crops {set(df['crop']) - set(HERBICIDE_CROPS)}")
    if (df["kg_ai_ha"] < 0).any() or df["kg_ai_ha"].isna().any():
        raise ValueError("herbicide table: negative or null application rate")
    present = {(y, r, c) for y, r, c in zip(df["year"], df["rotation"], df["crop"])}
    missing = {(y, r, c) for y in YEARS for r in ROTATIONS for c in HERBICIDE_CROPS} - present
    if missing:  # absence of a record must not silently become "no herbicide"
        raise ValueError(f"herbicide table: no record for {sorted(missing)[:5]}")


# --- calculation --------------------------------------------------------------------------
def rotation_year_inputs(fert: pd.DataFrame, herb: pd.DataFrame) -> pd.DataFrame:
    """Equal-area-weighted annual inputs per rotation (kg/ha)."""
    n = fert.groupby(["rotation", "year"], as_index=False)[["manufactured_n", "manure_n"]].sum()
    h = (herb.groupby(["rotation", "year"], as_index=False)["kg_ai_ha"].sum()
         .rename(columns={"kg_ai_ha": "herbicide"}))
    out = n.merge(h, on=["rotation", "year"], how="left")
    out["herbicide"] = out["herbicide"].fillna(0.0)  # a phase-less year is checked in validate_herbicide
    phases = out["rotation"].map(N_PHASES)
    for column in ("manufactured_n", "manure_n", "herbicide"):
        out[column] = out[column] / phases
    out["applied_n"] = out["manufactured_n"] + out["manure_n"]
    return out.sort_values(["rotation", "year"]).reset_index(drop=True)[
        ["rotation", "year", "manufactured_n", "manure_n", "applied_n", "herbicide"]]


def nine_year_means(by_year: pd.DataFrame) -> pd.DataFrame:
    grouped = by_year.groupby("rotation")
    out = grouped[["manufactured_n", "manure_n", "applied_n", "herbicide"]].mean()
    out["n_years"] = grouped["year"].count()
    return out.reset_index()


def reductions(summary: pd.DataFrame) -> dict:
    s = summary.set_index("rotation")
    def pct(col, rot):
        return 100.0 * (s.loc["2-yr", col] - s.loc[rot, col]) / s.loc["2-yr", col]
    return {
        "manufactured_n_pct": {r: pct("manufactured_n", r) for r in ("3-yr", "4-yr")},
        "herbicide_pct": {r: pct("herbicide", r) for r in ("3-yr", "4-yr")},
        "herbicide_pct_pooled": (pct("herbicide", "3-yr") + pct("herbicide", "4-yr")) / 2,
    }


# --- reconciliation -----------------------------------------------------------------------
@dataclass
class Check:
    quantity: str
    rotation: str
    computed: float
    reference: float
    source: str
    rule: str
    status: str  # MATCH | WITHIN_SEM | UNRECONCILED | INFO
    note: str = ""


def _status(computed: float, reference: float, step: float, sem: float | None) -> str:
    diff = abs(computed - reference)
    if diff <= step / 2 + 1e-9:
        return "MATCH"
    if sem is not None and diff <= sem:
        return "WITHIN_SEM"
    return "UNRECONCILED"


def reconcile(summary: pd.DataFrame, by_year: pd.DataFrame) -> list[Check]:
    s = summary.set_index("rotation")
    checks: list[Check] = []
    for (quantity, rotation), ref in PRD_TARGETS.items():
        value = float(s.loc[rotation, quantity])
        checks.append(Check(quantity, rotation, value, ref, "PRD s7.4 / roadmap Phase 6",
                            f"within half of last digit ({PRD_STEP[quantity] / 2:g})",
                            _status(value, ref, PRD_STEP[quantity], None)))
    for (quantity, rotation), (ref, sem, step) in PAPER_TEXT.items():
        value = float(s.loc[rotation, quantity])
        status = _status(value, ref, step, sem)
        note = ""
        if (quantity, rotation) == ("manufactured_n", "2-yr"):
            note = ("Gap traced to 2011 (see diagnostic). Table S3 gives maize 112 + soybean 0 = 56 "
                    "area-weighted; Fig. 1e plots about 112.")
        checks.append(Check(quantity, rotation, value, ref, "Davis 2012 Results text",
                            f"within half of last digit ({step / 2:g}), else within reported SEM ({sem:g})",
                            status, note))
    red = reductions(summary)["herbicide_pct_pooled"]
    checks.append(Check("herbicide_reduction_pct", "3-yr & 4-yr", red, PAPER_HERBICIDE_REDUCTION_PCT,
                        "Davis 2012 Results text", "within 0.5 percentage points",
                        _status(red, PAPER_HERBICIDE_REDUCTION_PCT, 1.0, None),
                        "mean of the 3-yr and 4-yr reductions"))
    # Diagnostic (hypothesis, not a correction): 2-yr 2011 as the maize phase alone.
    two = by_year[by_year["rotation"] == "2-yr"].set_index("year")["manufactured_n"].copy()
    fert_2011_maize = float(two.loc[2011]) * 2  # soybean N is 0 in 2011, so maize alone = 2 x weighted
    alt = (two.sum() - two.loc[2011] + fert_2011_maize) / len(two)
    checks.append(Check("manufactured_n", "2-yr (diagnostic: 2011 = maize N alone)", alt, 80.0,
                        "Davis 2012 Results text", "informational", "INFO",
                        "Not used in any output. If 2011 is read as 112, the 2-yr mean is about 80.7, "
                        "matching the paper's 80 +/- 3."))
    return checks


# --- provenance ---------------------------------------------------------------------------
def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_manifest(raw: Path) -> list[str]:
    """Return a list of problems; empty means every file matches its manifest checksum."""
    problems = []
    manifest = json.loads((raw / "MANIFEST.json").read_text())
    listed = {m["file"]: m for m in manifest}
    for name in INPUT_FILES:
        if name not in listed:
            problems.append(f"{name}: not in manifest")
        elif not (raw / name).exists():
            problems.append(f"{name}: file missing")
        elif sha256(raw / name) != listed[name]["sha256"]:
            problems.append(f"{name}: checksum mismatch")
    return problems


# --- pipeline -----------------------------------------------------------------------------
def run(raw: Path = DEFAULT_RAW, out: Path = DEFAULT_OUT) -> dict:
    problems = verify_manifest(raw)
    if problems:
        raise RuntimeError("raw inputs failed manifest check: " + "; ".join(problems))
    fert = load_fertilizer(raw / FERTILIZER_FILE)
    herb = load_herbicide(raw / HERBICIDE_FILE)
    validate_fertilizer(fert)
    validate_herbicide(herb)
    by_year = rotation_year_inputs(fert, herb)
    summary = nine_year_means(by_year)
    checks = reconcile(summary, by_year)

    out.mkdir(parents=True, exist_ok=True)
    by_year.round(6).to_csv(out / "management_by_year.csv", index=False)
    summary.round(6).to_csv(out / "management_summary.csv", index=False)
    pd.DataFrame([asdict(c) for c in checks]).round(6).to_csv(out / "reconciliation.csv", index=False)
    (out / "indicator_lineage.json").write_text(json.dumps(LINEAGE, indent=2) + "\n")
    manifest = {
        "script": Path(__file__).name,
        "script_sha256": sha256(Path(__file__)),
        "inputs": {n: sha256(raw / n) for n in INPUT_FILES},
        "python": platform.python_version(),
        "pandas": pd.__version__,
        "run_utc": datetime.now(UTC).isoformat(timespec="seconds"),
    }
    (out / "run_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return {"by_year": by_year, "summary": summary, "checks": checks, "reductions": reductions(summary)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--raw", type=Path, default=DEFAULT_RAW)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--strict", action="store_true", help="exit 1 if any check is UNRECONCILED")
    args = parser.parse_args()
    result = run(args.raw, args.out)
    pd.set_option("display.width", 160)
    print("Nine-year, equal-area-weighted means (kg/ha/yr), 2003-2011\n")
    print(result["summary"].round(3).to_string(index=False))
    print("\nReductions vs 2-yr (%):", json.dumps({k: (v if isinstance(v, float) else {a: round(b, 1) for a, b in v.items()})
                                                  for k, v in result["reductions"].items()}, default=float))
    print("\nReconciliation")
    for c in result["checks"]:
        print(f"  [{c.status:12}] {c.quantity:24} {c.rotation:38} computed {c.computed:9.3f}  ref {c.reference:8.3f}  ({c.source})")
    bad = [c for c in result["checks"] if c.status == "UNRECONCILED"]
    if bad:
        print(f"\n{len(bad)} UNRECONCILED check(s); see data/out/marsden/reconciliation.csv and README.")
    return 1 if (bad and args.strict) else 0


if __name__ == "__main__":
    sys.exit(main())
