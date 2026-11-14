"""One planned upload (file, manifest, checks) and the shared dry-run and upload loop."""

from dataclasses import dataclass
from pathlib import Path

from ingest.checks import CheckResult
from ingest.manifest import Manifest
from ingest.s3_store import AlreadyExistsError, upload_raw, verify_all

SHOW_LIMIT = 12  # lines printed before the rest are summarised


@dataclass(frozen=True)
class Item:
    path: Path
    manifest: Manifest
    checks: CheckResult
    source: str  # first folder under raw/ (for HLS, "hls/l30")
    key_name: str | None = None  # file name in the key, if it differs from the local name


def run_items(items: list[Item], client, bucket: str, execute: bool) -> int:
    """Report on the plan, then upload (or dry-run) every item. Returns a process exit code."""
    total = sum(i.manifest.size_bytes for i in items)
    print(f"{len(items)} files, {total / 1e6:.1f} MB")
    failed = [i for i in items if not i.checks.ok]
    for item in failed:
        print(f"CHECK FAILED {item.key_name or item.path.name}: {item.checks.problems}")
    if failed:
        print("Nothing was uploaded. Fix the failed checks first.")
        return 1
    print("all file checks passed")

    done = skipped = 0
    for item in items:
        try:
            key = upload_raw(client, bucket, item.path, item.manifest, source=item.source,
                             dry_run=not execute, key_name=item.key_name)
            done += 1
            if done <= SHOW_LIMIT:
                print(("  uploaded " if execute else "  would upload ") + key)
        except AlreadyExistsError as err:
            skipped += 1
            print(f"  already in S3, skipped: {err}")
    if done > SHOW_LIMIT:
        print(f"  ... and {done - SHOW_LIMIT} more")
    print(f"{'uploaded' if execute else 'would upload'} {done}, skipped {skipped} already in S3")
    if not execute:
        return 0
    problems = []
    for prefix in sorted({f"raw/{i.source}/" for i in items}):
        problems += verify_all(client, bucket, prefix=prefix)
    print(f"verify_all: {len(problems)} problems")
    for problem in problems:
        print("  -", problem)
    return 1 if problems else 0
