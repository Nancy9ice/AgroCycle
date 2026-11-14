"""One planned upload (file, manifest, checks) and the shared dry-run and upload loop."""

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path

from ingest.checks import CheckResult
from ingest.manifest import Manifest
from ingest.s3_store import AlreadyExistsError, _list_keys, upload_raw, verify_all

SHOW_LIMIT = 12  # lines printed before the rest are summarised
UPLOAD_WORKERS = 8
PROGRESS_EVERY = 1000


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

    existing = {o["Key"] for src in sorted({i.source for i in items})
                for o in _list_keys(client, bucket, f"raw/{src.split('/')[0]}/")}

    def send(item: Item):
        try:
            return upload_raw(client, bucket, item.path, item.manifest, source=item.source,
                              dry_run=not execute, key_name=item.key_name, existing=existing)
        except AlreadyExistsError as err:
            return err

    done = skipped = 0
    with ThreadPoolExecutor(UPLOAD_WORKERS) as pool:
        for n, result in enumerate(pool.map(send, items), 1):
            if isinstance(result, AlreadyExistsError):
                skipped += 1
                if skipped <= SHOW_LIMIT:
                    print(f"  already in S3, skipped: {result}")
                continue
            done += 1
            if done <= SHOW_LIMIT:
                print(("  uploaded " if execute else "  would upload ") + result)
            if n % PROGRESS_EVERY == 0:
                print(f"  ... {n} of {len(items)} handled", flush=True)
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
