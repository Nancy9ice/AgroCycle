"""Count the valid pixels of every HLS window. Dry run unless --load is given.

    uv run python -m transform.hls.run                  # read ~/agrocycle_hls (HLS_DIR), count, print a summary
    uv run python -m transform.hls.run --source s3      # read the stacks from S3 instead (slower)
    uv run python -m transform.hls.run --load           # also load hls_valid_pixels

One row per window, 16,560 in all: every stack, including the windows with no data. A CSV copy goes to
data/out/hls/ (gitignored). `--load` validates the frame first, applies new schema/*.sql, then loads.
"""

import argparse
import sys
from pathlib import Path

import pandas as pd
from botocore.exceptions import BotoCoreError, ClientError

from common.schemas import TABLES
from transform.field_schema import ROOT
from transform.hls import counts
from transform.hls.sources import LocalSource, S3Source

OUT_DIR = ROOT / "data" / "out" / "hls"


def summary(frame: pd.DataFrame) -> list[str]:
    observed = frame[frame["status"] == "observed"]
    by_sensor = frame.groupby(["sensor", "status"]).size().to_dict()
    status = frame["status"]
    lines = [
        (f"{len(frame)} windows ({int((status == 'observed').sum())} observed, "
         f"{int((status == 'no_data').sum())} no data) for {frame['field_id'].nunique()} fields"),
        f"  by sensor and status: {by_sensor}",
        (f"  pixels in the polygons: total {int(frame['total_pixels'].sum())}, valid {int(frame['valid_pixels'].sum())}, "
         f"flagged {int(frame['flagged_pixels'].sum())}, fill {int(frame['fill_pixels'].sum())}"),
        (f"  observed windows with no valid pixel: {int((observed['valid_pixels'] == 0).sum())}; "
         f"with at least half valid: {int((observed['valid_share'] >= 0.5).sum())}"),
    ]
    return lines


def load_table(frame: pd.DataFrame) -> None:
    from common.config import clickhouse_client
    from common.load import load
    from common.migrate import migrate

    client = clickhouse_client()
    applied = migrate(client)
    if applied:
        print("applied: " + ", ".join(applied))
    result = load(client, "hls_valid_pixels", frame)
    print(f"loaded hls_valid_pixels: {result.rows} rows, run {result.load_id}")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--source", choices=("local", "s3"), default="local")
    parser.add_argument("--dir", type=Path, help="the HLS pull folder (default HLS_DIR or ~/agrocycle_hls)")
    parser.add_argument("--out", type=Path, default=OUT_DIR, help="folder for the CSV copy")
    parser.add_argument("--load", action="store_true", help="load into ClickHouse (default: dry run)")
    args = parser.parse_args(argv)
    try:
        if args.source == "s3":
            from common.config import s3_bucket, s3_client

            source = S3Source(s3_client(), s3_bucket())
        else:
            source = LocalSource(args.dir)
        frame = counts.count_windows(source)
        if frame.empty:
            raise ValueError("no HLS windows found")
        TABLES["hls_valid_pixels"].schema.validate(frame)  # checked before anything is written or loaded
    except (ValueError, RuntimeError, OSError, KeyError, StopIteration, BotoCoreError, ClientError) as err:
        print(f"hls: {err}")
        return 1
    except Exception as err:
        if type(err).__module__.startswith("pandera"):
            print(f"hls: the counts fail their schema:\n{err}")
            return 1
        raise
    args.out.mkdir(parents=True, exist_ok=True)
    frame.to_csv(args.out / "hls_valid_pixels.csv", index=False)
    print("\n".join(summary(frame)))
    if args.load:
        load_table(frame)
    else:
        print("dry run: nothing loaded (use --load)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
