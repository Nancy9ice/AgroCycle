"""Validate and load DS2's indicator CSVs into ClickHouse. Dry run unless --load is given.

    uv run python -m transform.indicators.load                    # read data/out/indicators/, check, report
    uv run python -m transform.indicators.load --dir DIR --load

Reads the three files DS2's runner writes (`field_indicators.csv`, `soil_properties.csv`,
`indicator_lineage.csv`, plus `run_manifest.json` when present). Refuses, before touching the database,
when an indicator has no lineage row, a field is unknown, or the files disagree with the manifest.
Lineage loads first so the loader's own orphan check can pass. Blank cells are read as empty text or null
by column, never as the text "nan".
"""

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

from common.schemas import TABLES
from transform.field_schema import ROOT, load_fields

DEFAULT_DIR = ROOT / "data" / "out" / "indicators"
FILES = ("indicator_lineage", "field_indicators", "soil_properties")  # load order: lineage first

NUMBERS = {"field_indicators": ["value"], "soil_properties": ["share_pct", "value_num"]}
DATES = {"field_indicators": ["window_start", "window_end"]}
INTEGERS = {"field_indicators": ["valid_obs"]}
NULLABLE_TEXT = {"field_indicators": ["unknown_reason"], "soil_properties": ["value_text"]}


def read_frames(directory: Path) -> dict[str, pd.DataFrame]:
    frames = {}
    for name in FILES:
        frame = pd.read_csv(directory / f"{name}.csv", dtype=str, keep_default_na=False)
        for column in NUMBERS.get(name, []):
            frame[column] = pd.to_numeric(frame[column].replace("", None))
        for column in DATES.get(name, []):
            # pandas 3 parses to microseconds; the schemas (and every other frame here) use nanoseconds
            frame[column] = pd.to_datetime(frame[column].replace("", None)).astype("datetime64[ns]")
        for column in INTEGERS.get(name, []):
            frame[column] = pd.to_numeric(frame[column].replace("", None)).astype("Int64")
        for column in NULLABLE_TEXT.get(name, []):
            frame[column] = frame[column].where(frame[column] != "", None)
        frames[name] = frame
    return frames


def problems(frames: dict[str, pd.DataFrame], manifest: dict | None, field_ids: set[str]) -> list[str]:
    found = [f"{name} is empty" for name in FILES if frames[name].empty]
    lineage = set(frames["indicator_lineage"]["indicator_id"])
    used = set(frames["field_indicators"]["indicator_id"]) | set(frames["soil_properties"]["indicator_id"])
    missing = sorted(used - lineage)
    if missing:
        found.append(f"{len(missing)} indicators have no lineage row: {', '.join(missing)}")
    unknown_fields = sorted((set(frames["field_indicators"]["field_id"]) | set(frames["soil_properties"]["field_id"])) - field_ids)
    if unknown_fields:
        found.append(f"fields not in fields.geojson: {', '.join(unknown_fields)}")
    run_ids = {r for f in FILES for r in frames[f]["run_id"].unique()}
    if len(run_ids) != 1:
        found.append(f"the files come from {len(run_ids)} runs: {sorted(run_ids)}")
    if manifest:
        for name in FILES:
            if manifest.get("rows", {}).get(name) != len(frames[name]):
                found.append(f"{name}: {len(frames[name])} rows, the manifest says {manifest.get('rows', {}).get(name)}")
        if manifest.get("run_id") not in run_ids:
            found.append(f"run_manifest.json run_id {manifest.get('run_id')} is not the files' run_id")
    return found


def load_all(frames: dict[str, pd.DataFrame]) -> None:
    from common.config import clickhouse_client
    from common.load import load
    from common.migrate import migrate

    for name in FILES:
        TABLES[name].schema.validate(frames[name])  # every frame is checked before any table is touched
    client = clickhouse_client()
    applied = migrate(client)
    if applied:
        print("applied: " + ", ".join(applied))
    for name in FILES:
        result = load(client, name, frames[name])
        print(f"loaded {name}: {result.rows} rows, run {result.load_id}")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--dir", type=Path, default=DEFAULT_DIR, help="the folder holding DS2's CSVs")
    parser.add_argument("--load", action="store_true", help="load into ClickHouse (default: dry run)")
    args = parser.parse_args(argv)
    try:
        frames = read_frames(args.dir)
    except (OSError, ValueError) as err:  # a missing folder, or an empty or unreadable CSV (EmptyDataError)
        print(f"indicator load: {err}")
        return 1
    manifest_path = args.dir / "run_manifest.json"
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else None
    found = problems(frames, manifest, set(load_fields()["field_id"]))
    print(", ".join(f"{name} {len(frames[name])} rows" for name in FILES))
    for line in found:
        print(f"REFUSED: {line}")
    if found:
        return 1
    if args.load:
        load_all(frames)
    else:
        print("dry run: nothing loaded (use --load)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
