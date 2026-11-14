"""Run one source's extraction into S3.  Dry run unless --execute is given.

Usage:
    uv run python -m ingest.run cdl              # check everything, write nothing
    uv run python -m ingest.run cdl --execute    # upload to raw/ (cannot be undone)
    uv run python -m ingest.run marsden --dir ~/agrocycle_marsden
"""

import argparse
import sys
from pathlib import Path

from common.config import s3_bucket, s3_client
from ingest import cdl, hls, marsden, power, ssurgo
from ingest.items import run_items

PLANNERS = {"cdl": cdl.plan, "marsden": marsden.plan, "power-first": power.plan_first_pull,
            "power-full": power.plan_full,
            "ssurgo-first": ssurgo.plan_first_pull,
            "ssurgo-full": ssurgo.plan_all,
            "hls-first": hls.plan_first_pull}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("source", choices=sorted(PLANNERS))
    parser.add_argument("--execute", action="store_true", help="upload for real (default: dry run)")
    parser.add_argument("--dir", type=Path, help="folder holding the downloaded files")
    args = parser.parse_args(argv)
    try:
        items = PLANNERS[args.source](args.dir)
    except (RuntimeError, ValueError) as err:
        print(f"{args.source}: {err}")
        return 1
    return run_items(items, s3_client(), s3_bucket(), args.execute)


if __name__ == "__main__":
    sys.exit(main())
