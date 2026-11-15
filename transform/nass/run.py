"""Clean the NASS county statistics and load county_stats. Dry run unless --load is given.

    uv run python -m transform.nass.run              # clean, check, print the report (local pull folder)
    uv run python -m transform.nass.run --s3         # read the raw files from S3 instead (read-only)
    uv run python -m transform.nass.run --load       # also apply new schema/*.sql and load county_stats

The raw files are never changed. A hard schema failure stops the run before anything is written.
"""

import argparse
import sys
from pathlib import Path

import pandas as pd

from transform.field_schema import ROOT
from transform.nass import clean

OUT_DIR = ROOT / "data" / "out" / "nass"


def summary(frame: pd.DataFrame) -> list[str]:
    withheld = frame[frame["value_status"] == "withheld"]
    lines = [
        (f"county_stats: {len(frame)} rows, {frame['county'].nunique()} counties, "
         f"{frame['commodity'].nunique()} commodities, years {frame['year'].min()}-{frame['year'].max()}"),
        f"  reported {int((frame['value_status'] == 'reported').sum())}, withheld {len(withheld)} (kept as null)",
    ]
    for _, r in withheld.iterrows():
        lines.append(f"  withheld: {r['county']} {r['commodity']} {r['class_desc']} {r['statistic']} {r['year']}")
    span = frame.groupby(["county", "commodity"])["year"].agg(["min", "max", "nunique"])
    for (county, commodity), r in span.iterrows():
        lines.append(f"  {county:5} {commodity:8} {r['min']}-{r['max']} ({r['nunique']} years)")
    return lines


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--load", action="store_true", help="load into ClickHouse (default: dry run)")
    parser.add_argument("--s3", action="store_true", help="read raw files from S3, not the local pull folder")
    parser.add_argument("--dir", type=Path, help="folder holding the raw files")
    args = parser.parse_args(argv)
    try:
        if args.s3:
            from common.config import s3_bucket, s3_client

            bodies = clean.read_s3(s3_client(), s3_bucket())
        else:
            bodies = clean.read_local(args.dir)
        frame = clean.build(bodies)
    except RuntimeError as err:
        print(f"nass: {err}")
        return 1
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    frame.to_csv(OUT_DIR / "county_stats.csv", index=False)
    print("\n".join(summary(frame)))
    if not args.load:
        print("dry run: nothing loaded (use --load)")
        return 0
    from common.config import clickhouse_client
    from common.load import load
    from common.migrate import migrate

    client = clickhouse_client()
    print("migrations applied:", migrate(client) or "none new")
    print(load(client, "county_stats", frame))
    return 0


if __name__ == "__main__":
    sys.exit(main())
