"""Build and load the naip_tiles index. Dry run unless --load is given.

    uv run python -m transform.naip.run            # read the manifests from S3, check, print the report
    uv run python -m transform.naip.run --load     # also apply new schema/*.sql and load naip_tiles
"""

import argparse
import sys

import pandas as pd

from transform.naip import build


def summary(frame: pd.DataFrame) -> list[str]:
    multi = frame.groupby("field_id").size()
    dates = frame.groupby("flight_date").size()
    return [
        f"naip_tiles: {len(frame)} rows, {frame['field_id'].nunique()} fields, year {sorted(int(y) for y in frame['year'].unique())}",
        f"  fields cut from 2+ tiles: {sorted(multi[multi > 1].index)}",
        "  flight dates: " + ", ".join(f"{d:%Y-%m-%d} ({n})" for d, n in dates.items()),
        f"  total chip size {frame.drop_duplicates('s3_key')['size_bytes'].sum() / 1e6:.1f} MB",
    ]


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--load", action="store_true", help="load into ClickHouse (default: dry run)")
    args = parser.parse_args(argv)
    from common.config import s3_bucket, s3_client

    try:
        frame = build.build(build.read_s3_manifests(s3_client(), s3_bucket()))
    except build.NaipBuildError as err:
        print(f"naip: {err}")
        return 1
    print("\n".join(summary(frame)))
    if not args.load:
        print("dry run: nothing loaded (use --load)")
        return 0
    from common.config import clickhouse_client
    from common.load import load
    from common.migrate import migrate

    client = clickhouse_client()
    print("migrations applied:", migrate(client) or "none new")
    print(load(client, "naip_tiles", frame))
    return 0


if __name__ == "__main__":
    sys.exit(main())
