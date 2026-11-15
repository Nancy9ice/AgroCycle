"""Validate DS2's Marsden reproduction and load it into ClickHouse (roadmap Phase 6, DE). Dry run unless --load.

    uv run python -m transform.marsden_load                    # read data/out/marsden/, validate, report
    uv run python -m transform.marsden_load --reproduce        # rerun DS2's script first (needs the raw files)
    uv run python -m transform.marsden_load --check-s3 --load  # also compare input checksums with S3, then load

DS2's reproduction is not changed here. The DE reads its outputs, validates them with his Pandera schemas
and its own checks, turns the two wide tables into one long table (one row per rotation, period and metric,
each with its indicator id), maps his four lineage rows onto the 15 columns of `indicator_lineage` by the
convention his own runner uses for POWER, and loads: lineage first, then the management table and the
reconciliation record. The one UNRECONCILED check stays UNRECONCILED; no value is edited.
"""

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
from botocore.exceptions import BotoCoreError, ClientError

from common.schemas import TABLES
from transform.marsden import marsden_repro
from transform.marsden.schemas import validate_outputs

OUT_DIR = marsden_repro.DEFAULT_OUT
RAW_PREFIX = "raw/marsden/pone.0047149-supplement/2026-11-13"
SOURCE_ID = "pone.0047149"  # Davis et al. (2012), PLOS ONE 7(10): e47149, and its supporting information
FIRST_YEAR, LAST_YEAR = 2003, 2011

# the wide column of DS2's CSVs -> the indicator id in his lineage rows
INDICATORS = {
    "manufactured_n": "marsden_manufactured_n_kg_ha_yr",
    "manure_n": "marsden_manure_n_kg_ha_yr",
    "applied_n": "marsden_applied_n_kg_ha_yr",
    "herbicide": "marsden_herbicide_kg_ai_ha_yr",
}
EXPECTED_ROWS = {"by_year": 27, "summary": 3, "reconciliation": 20, "lineage": 4}
LINEAGE_COLUMNS = ["indicator_id", "label", "source_ids", "variables", "formula", "aggregation_window",
                   "spatial_support", "scale", "resolution", "evidence_type", "missing_data_rule",
                   "interpretation", "limitation", "code_version", "run_id"]


@dataclass
class Outputs:
    by_year: pd.DataFrame
    summary: pd.DataFrame
    reconciliation: pd.DataFrame
    lineage: list[dict]
    run_manifest: dict


def read_outputs(out: Path) -> Outputs:
    return Outputs(
        pd.read_csv(out / "management_by_year.csv"),
        pd.read_csv(out / "management_summary.csv"),
        pd.read_csv(out / "reconciliation.csv", keep_default_na=False),  # a blank note is text, not null
        json.loads((out / "indicator_lineage.json").read_text()),
        json.loads((out / "run_manifest.json").read_text()),
    )


def problems(outputs: Outputs) -> list[str]:
    """DS2's own schema findings, then the DE's: row counts, coverage and the indicator ids."""
    found = validate_outputs(outputs.by_year, outputs.summary, outputs.reconciliation, outputs.lineage)
    counts = {"by_year": len(outputs.by_year), "summary": len(outputs.summary),
              "reconciliation": len(outputs.reconciliation), "lineage": len(outputs.lineage)}
    found += [f"{name}: {counts[name]} rows, expected {want}" for name, want in EXPECTED_ROWS.items() if counts[name] != want]
    ids = {row.get("indicator_id") for row in outputs.lineage}
    missing = sorted(set(INDICATORS.values()) - ids)
    if missing:
        found.append(f"lineage has no row for: {', '.join(missing)}")
    years = sorted(outputs.by_year["year"].unique()) if "year" in outputs.by_year else []
    if years != list(range(FIRST_YEAR, LAST_YEAR + 1)):
        found.append(f"by-year rows cover {years}, expected {FIRST_YEAR}-{LAST_YEAR}")
    return found


def to_long(outputs: Outputs) -> pd.DataFrame:
    """One row per rotation, period and metric. Lossless: every cell of both wide tables appears once."""
    units = {row["indicator_id"]: row["unit"] for row in outputs.lineage}
    rows = []
    for record in outputs.by_year.itertuples(index=False):
        for metric, indicator in INDICATORS.items():
            rows.append((record.rotation, int(record.year), int(record.year), metric, indicator,
                         float(getattr(record, metric)), units[indicator], 1))
    for record in outputs.summary.itertuples(index=False):
        for metric, indicator in INDICATORS.items():
            rows.append((record.rotation, FIRST_YEAR, LAST_YEAR, metric, indicator,
                         float(getattr(record, metric)), units[indicator], int(record.n_years)))
    frame = pd.DataFrame(rows, columns=["rotation", "first_year", "last_year", "metric", "indicator_id",
                                        "value", "unit", "n_years"])
    frame["evidence_type"] = "experimental"
    frame["source_id"] = SOURCE_ID
    return frame.sort_values(["rotation", "metric", "first_year", "last_year"]).reset_index(drop=True)


def lineage_frame(outputs: Outputs) -> pd.DataFrame:
    """His four rows in the 15 columns of indicator_lineage, by the convention his POWER runner uses:
    label from the id, interpretation = the formula, resolution = the spatial scale text, the temporal window
    as the aggregation window. `scale` is `site` (one research site); the code version and run id come from
    his run manifest, so a changed script or rerun is visible in the data."""
    sha = outputs.run_manifest["script_sha256"]
    stamp = outputs.run_manifest["run_utc"].replace("-", "").replace(":", "").replace("+0000", "Z").replace("+00:00", "Z")
    rows = []
    for row in outputs.lineage:
        rows.append({
            "indicator_id": row["indicator_id"],
            "label": row["indicator_id"].replace("_", " "),
            "source_ids": json.dumps([row["source"]]),
            "variables": json.dumps([row["variables"]]),  # his field is one descriptive string
            "formula": row["formula"],
            "aggregation_window": row["temporal_window"],
            "spatial_support": row["spatial_scale"],
            "scale": "site",
            "resolution": row["spatial_scale"],
            "evidence_type": row["evidence_type"],
            "missing_data_rule": row["missing_data_rule"],
            "interpretation": row["formula"],
            "limitation": row["limitation"],
            "code_version": f"marsden_repro@{sha[:12]}",
            "run_id": f"ds2-marsden-{stamp}",
        })
    return pd.DataFrame(rows, columns=LINEAGE_COLUMNS)


def reconciliation_frame(outputs: Outputs) -> pd.DataFrame:
    frame = outputs.reconciliation.copy()
    frame["note"] = frame["note"].astype(str)
    return frame[["quantity", "rotation", "computed", "reference", "source", "rule", "status", "note"]]


def checksum_problems(run_manifest: dict, client, bucket: str) -> list[str]:
    """Each raw input his run used must have the SHA-256 recorded by the Phase 1 upload."""
    found = []
    for name, sha in run_manifest["inputs"].items():
        key = f"{RAW_PREFIX}/{name}.manifest.json"
        remote = json.loads(client.get_object(Bucket=bucket, Key=key)["Body"].read())["sha256"]
        if remote != sha:
            found.append(f"{name}: his run used {sha[:12]}, S3 holds {remote[:12]}")
    return found


def summary(outputs: Outputs, long_frame: pd.DataFrame) -> list[str]:
    nine = outputs.summary.set_index("rotation")
    status = outputs.reconciliation["status"].value_counts().to_dict()
    lines = [
        (f"{len(outputs.by_year)} by-year rows and {len(outputs.summary)} summary rows -> {len(long_frame)} long rows; "
         f"{len(outputs.lineage)} lineage rows; {len(outputs.reconciliation)} reconciliation checks {status}"),
        "  nine-year means (applied N, herbicide): "
        + "; ".join(f"{r} {nine.loc[r, 'applied_n']:.1f}, {nine.loc[r, 'herbicide']:.3f}" for r in nine.index),
    ]
    gaps = outputs.reconciliation[outputs.reconciliation["status"] == "UNRECONCILED"]
    lines += [f"  UNRECONCILED, kept visible: {r.quantity} {r.rotation}: computed {r.computed:g}, {r.source} says {r.reference:g}"
              for r in gaps.itertuples()]
    return lines


def load_all(lineage: pd.DataFrame, management: pd.DataFrame, reconciliation: pd.DataFrame) -> None:
    from common.config import clickhouse_client
    from common.load import load
    from common.migrate import migrate

    frames = (("indicator_lineage", lineage), ("marsden_management", management),
              ("marsden_reconciliation", reconciliation))
    for table, frame in frames:
        TABLES[table].schema.validate(frame)  # every frame is checked before any table is touched
    client = clickhouse_client()
    applied = migrate(client)
    if applied:
        print("applied: " + ", ".join(applied))
    for table, frame in frames:
        result = load(client, table, frame)
        print(f"loaded {table}: {result.rows} rows, run {result.load_id}")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--out", type=Path, default=OUT_DIR, help="DS2's output folder (default data/out/marsden)")
    parser.add_argument("--reproduce", action="store_true", help="rerun DS2's script first (needs the raw files)")
    parser.add_argument("--check-s3", action="store_true", help="compare input checksums with the S3 manifests")
    parser.add_argument("--load", action="store_true", help="load into ClickHouse (default: dry run)")
    args = parser.parse_args(argv)
    try:
        if args.reproduce:
            marsden_repro.run(out=args.out)
        outputs = read_outputs(args.out)
        found = problems(outputs)
        if args.check_s3:
            from common.config import s3_bucket, s3_client

            found += checksum_problems(outputs.run_manifest, s3_client(), s3_bucket())
    except (ValueError, RuntimeError, OSError, KeyError, BotoCoreError, ClientError) as err:
        print(f"marsden: {err}  (run with --reproduce to build DS2's outputs)")
        return 1
    for line in found:
        print(f"REFUSED: {line}")
    if found:
        return 1
    long_frame = to_long(outputs)
    print("\n".join(summary(outputs, long_frame)))
    if args.load:
        load_all(lineage_frame(outputs), long_frame, reconciliation_frame(outputs))
    else:
        print("dry run: nothing loaded (use --load)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
