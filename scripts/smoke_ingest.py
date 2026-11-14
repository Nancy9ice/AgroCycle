"""Check the upload tooling against the real bucket, under smoke/ingest-check/.

Objects cannot be deleted by this user, so the script writes one fixed key (about 100 bytes)
once. Later runs find it and prove the no-overwrite behaviour instead. It checks:
  1. a missing key answers a HEAD request with 404 (not 403)
  2. upload, read-back checksum and manifest work
  3. a second upload is refused by the pre-check
  4. S3's own conditional write refuses an overwrite (bypassing the pre-check)
  5. the user can list objects, which verify_all needs

Usage: uv run python -m scripts.smoke_ingest
"""

import sys
import tempfile
from pathlib import Path

from common.config import s3_bucket, s3_client
from ingest.manifest import build_manifest
from ingest.s3_store import (
    AlreadyExistsError,
    _put,
    key_exists,
    upload_raw,
    verify_all,
)

ROOT = "smoke"
SOURCE = "ingest-check"
CONTENT = b"agrocycle ingest smoke test\n"
FIELDS = {
    "source_url": "local test file",
    "product": "ingest smoke test",
    "version": "v1",
    "retrieval_date": "2026-11-14",
    "licence": "none (test data)",
    "subset": {"kind": "none"},
    "evidence_type": "assumption",
    "scale": "none",
    "notes": "written by scripts/smoke_ingest.py; safe to ignore",
}


def main() -> int:
    client, bucket = s3_client(), s3_bucket()
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "ingest_check.txt"
        path.write_bytes(CONTENT)
        manifest = build_manifest(path, **FIELDS)

        absent = f"{ROOT}/{SOURCE}/never-written-{manifest.sha256[:8]}"
        print(f"1. missing key reported as missing: {not key_exists(client, bucket, absent)}")

        try:
            key = upload_raw(client, bucket, path, manifest, source=SOURCE, root=ROOT)
            print(f"2. uploaded and verified: {key}")
        except AlreadyExistsError as err:
            key = str(err).removesuffix(".manifest.json")
            print(f"2. already uploaded by an earlier run: {key}")

        try:
            upload_raw(client, bucket, path, manifest, source=SOURCE, root=ROOT)
            print("3. FAIL: a second upload was accepted")
            return 1
        except AlreadyExistsError:
            print("3. second upload refused by the pre-check")

        try:
            _put(client, bucket, key, b"overwrite attempt")
            print("4. FAIL: S3 accepted an overwrite")
            return 1
        except AlreadyExistsError:
            print("4. S3 conditional write refused the overwrite")

        problems = verify_all(client, bucket, prefix=f"{ROOT}/{SOURCE}/")
        print(f"5. verify_all found {len(problems)} problems")
        for problem in problems:
            print("   -", problem)
        return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
