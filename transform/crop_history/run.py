"""Build the Phase 3 tables from the CDL clips. Dry run unless --load is given.

    uv run python -m transform.crop_history.run                 # compute, write CSVs, print a summary
    uv run python -m transform.crop_history.run --load          # also load into ClickHouse
    uv run python -m transform.crop_history.run --dir ~/agrocycle_cdl --out data/out/crop_history

The CDL clips are the Phase 1 pull (CDL_DIR, default ~/agrocycle_cdl). Output CSVs go to
data/out/crop_history/ (gitignored). --load applies any new schema/*.sql, then loads the four tables
through common.load, one at a time: each load is atomic, the four together are not.
"""

import argparse
import sys
from pathlib import Path

import pandas as pd

from common.schemas import TABLES
from ingest.cdl import default_dir
from transform.crop_history import zonal
from transform.crop_history.build import CropFrames, crop_frames, fields_frame
from transform.field_schema import ROOT, load_fields

OUT_DIR = ROOT / "data" / "out" / "crop_history"
# What Phase 0 expected of each field (the DE's working rules), to compare with DS1's rules.
EXPECTED_CLASS = {
    "in-domain: maize-soybean rotation": "rotation",
    "out-of-domain: continuous corn": "continuous_corn",
    "out-of-domain: pasture-hay": "pasture_hay",
    "out-of-domain: mixed-non-rotation": "mixed",
}


def write_csvs(out: Path, frames: dict[str, pd.DataFrame]) -> None:
    out.mkdir(parents=True, exist_ok=True)
    for name, frame in frames.items():
        frame.to_csv(out / f"{name}.csv", index=False)


def summary(fields: pd.DataFrame, crops: CropFrames) -> list[str]:
    lines = ["field class under DS1's rules v1.0:"]
    counts = crops.rotation["field_class"].value_counts()
    lines += [f"  {name:16} {n}" for name, n in counts.items()]
    status = crops.history["status"].value_counts()
    lines.append("year labels: " + ", ".join(f"{k} {v}" for k, v in status.items()))
    if crops.unlisted_codes:
        listed = ", ".join(f"{c} {n}" for c, n in sorted(crops.unlisted_codes.items()))
        lines.append(f"codes DS1's rules do not mention (kept as other_crop, flagged): {listed}")
    merged = fields.merge(crops.rotation[["field_id", "field_class"]], on="field_id")
    merged["expected"] = merged["domain_note"].map(EXPECTED_CLASS)
    unmapped = merged[merged["expected"].isna()]
    merged = merged.dropna(subset=["expected"])
    differs = merged[merged["expected"] != merged["field_class"]]
    lines.append(f"fields whose class differs from the Phase 0 label: {len(differs)} of {len(merged)}")
    if len(unmapped):
        lines.append(f"fields with a Phase 0 note this check does not know: {', '.join(unmapped['field_id'])}")
    lines += [
        f"  {r.field_id}: Phase 0 '{r.expected}', rules '{r.field_class}'" for r in differs.itertuples()
    ]
    return lines


def load_all(fields: pd.DataFrame, crops: CropFrames) -> None:
    from common.config import clickhouse_client
    from common.load import load
    from common.migrate import migrate

    tables = (
        ("fields", fields),
        ("crop_class_shares", crops.shares),
        ("crop_history", crops.history),
        ("crop_rotation", crops.rotation),
    )
    for table, frame in tables:  # every frame is checked before any table is touched
        TABLES[table].schema.validate(frame)
    client = clickhouse_client()
    applied = migrate(client)
    if applied:
        print("applied: " + ", ".join(applied))
    for table, frame in tables:
        result = load(client, table, frame)
        print(f"loaded {table}: {result.rows} rows, run {result.load_id}")
    problems = consistency_problems(client)
    for problem in problems:
        print(f"INCONSISTENT: {problem}")
    if problems:
        raise RuntimeError("the four tables do not describe the same fields; rerun the load")


def consistency_problems(client) -> list[str]:
    """The four tables are loaded one at a time, so check afterwards that they agree."""
    problems = []
    for table in ("crop_class_shares", "crop_history", "crop_rotation"):
        orphans = client.query(
            f"SELECT count() FROM `{table}` WHERE field_id NOT IN (SELECT field_id FROM fields)"
        ).result_rows[0][0]
        missing = client.query(
            f"SELECT count() FROM fields WHERE field_id NOT IN (SELECT field_id FROM `{table}`)"
        ).result_rows[0][0]
        if orphans or missing:
            problems.append(f"{table}: {orphans} rows for unknown fields, {missing} fields without rows")
    versions = client.query("SELECT uniqExact(rule_version) FROM crop_history").result_rows[0][0]
    if versions != 1:
        problems.append(f"crop_history holds {versions} rule versions")
    return problems


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--dir", type=Path, help="the CDL pull folder (default CDL_DIR or ~/agrocycle_cdl)")
    parser.add_argument("--out", type=Path, default=OUT_DIR, help="folder for the CSV copies")
    parser.add_argument("--load", action="store_true", help="load into ClickHouse (default: dry run)")
    args = parser.parse_args(argv)
    try:
        gdf = load_fields()
        clip_map = zonal.clips(args.dir or default_dir())
        crops = crop_frames(gdf, clip_map)
    except (ValueError, RuntimeError, OSError) as err:  # OSError covers unreadable or missing clips
        print(f"crop history: {err}")
        return 1
    fields = fields_frame(gdf)
    write_csvs(args.out, {"fields": fields, "crop_class_shares": crops.shares,
                          "crop_history": crops.history, "crop_rotation": crops.rotation})
    print(f"{len(fields)} fields, {len(crops.shares)} class-share rows, {len(crops.history)} field-years")
    print("\n".join(summary(fields, crops)))
    if args.load:
        load_all(fields, crops)
    else:
        print("dry run: nothing loaded (use --load)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
