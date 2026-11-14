"""Run one source's extraction into S3.  Dry run unless --execute is given.

Usage:
    uv run python -m ingest.run cdl             # check everything, write nothing
    uv run python -m ingest.run cdl --execute   # upload to raw/ (cannot be undone)
"""

import argparse
import sys
from pathlib import Path

from common.config import s3_bucket, s3_client
from ingest import cdl
from ingest.s3_store import AlreadyExistsError, upload_raw, verify_all


def run_cdl(base: Path | None, execute: bool) -> int:
    items = cdl.plan(base)
    total = sum(i.manifest.size_bytes for i in items)
    tifs = [i for i in items if i.path.suffix == ".tif"]
    print(f"cdl: {len(tifs)} GeoTIFFs + {len(items) - len(tifs)} class tables, "
          f"{total / 1e6:.1f} MB (budget {cdl.BUDGET_BYTES / 1e6:.0f} MB)")

    failed = [i for i in items if not i.checks.ok or i.manifest.size_bytes == 0]
    for item in failed:
        print(f"CHECK FAILED {item.path.name}: {item.checks.problems or 'missing file'}")
    if failed:
        return 1
    print("all file checks passed")

    client, bucket = s3_client(), s3_bucket()
    uploaded = skipped = 0
    for item in items:
        try:
            key = upload_raw(client, bucket, item.path, item.manifest, source=cdl.SOURCE,
                             dry_run=not execute)
            uploaded += 1
            if uploaded <= 3 or not execute:
                print(("  uploaded " if execute else "  would upload ") + key)
        except AlreadyExistsError as err:
            skipped += 1
            print(f"  already in S3, skipped: {err}")
    verb = "uploaded" if execute else "would upload"
    print(f"{verb} {uploaded}, skipped {skipped} already in S3")
    if execute:
        problems = verify_all(client, bucket, prefix=f"raw/{cdl.SOURCE}/")
        print(f"verify_all over raw/{cdl.SOURCE}/: {len(problems)} problems")
        for problem in problems:
            print("  -", problem)
        return 1 if problems else 0
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("source", choices=["cdl"])
    parser.add_argument("--execute", action="store_true", help="upload for real (default: dry run)")
    parser.add_argument("--dir", type=Path, help="folder holding the downloaded files")
    args = parser.parse_args(argv)
    return run_cdl(args.dir, args.execute)


if __name__ == "__main__":
    sys.exit(main())
