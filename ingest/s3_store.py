"""Write raw files to S3 without ever overwriting, and verify them by checksum.

Layout: raw/<source>/<product-version>/<retrieval-date>/<file> with <file>.manifest.json
beside it. The IAM user cannot delete objects, so a bad upload stays: check with dry_run first.
"""

import base64
import hashlib
from pathlib import Path

from botocore.exceptions import ClientError

from ingest.manifest import Manifest, sha256_file

MAX_PUT_BYTES = 4 * 1024**3  # one put_object call; larger files need multipart
MANIFEST_SUFFIX = ".manifest.json"
_MISSING = {"404", "NoSuchKey", "NotFound"}
_EXISTS = {"PreconditionFailed", "412"}


class AlreadyExistsError(RuntimeError):
    """The key already holds an object; raw files are immutable."""


class ChecksumMismatchError(RuntimeError):
    """A file does not match the SHA-256 recorded in its manifest."""


def raw_key(
    source: str, version: str, retrieval_date: str, filename: str, root: str = "raw"
) -> str:
    return f"{root}/{source}/{version}/{retrieval_date}/{filename}"


def manifest_key(key: str) -> str:
    return key + MANIFEST_SUFFIX


def key_exists(client, bucket: str, key: str) -> bool:
    try:
        client.head_object(Bucket=bucket, Key=key)
    except ClientError as err:
        code = err.response["Error"]["Code"]
        if code in _MISSING:
            return False
        if code == "403":
            raise PermissionError(
                f"S3 refused to say whether {key} exists (403). The user may lack "
                "s3:ListBucket, which S3 needs to report a missing key."
            ) from err
        raise
    return True


def _put(client, bucket: str, key: str, body, sha256_hex: str | None = None) -> None:
    args = {"Bucket": bucket, "Key": key, "Body": body, "IfNoneMatch": "*"}
    if sha256_hex:
        args["ChecksumSHA256"] = base64.b64encode(bytes.fromhex(sha256_hex)).decode()
    try:
        client.put_object(**args)
    except ClientError as err:
        if err.response["Error"]["Code"] in _EXISTS:
            raise AlreadyExistsError(key) from err
        raise


def sha256_object(client, bucket: str, key: str) -> str:
    digest = hashlib.sha256()
    for chunk in client.get_object(Bucket=bucket, Key=key)["Body"].iter_chunks(1 << 20):
        digest.update(chunk)
    return digest.hexdigest()


def verify_object(client, bucket: str, key: str, expected_sha256: str) -> None:
    actual = sha256_object(client, bucket, key)
    if actual != expected_sha256:
        raise ChecksumMismatchError(f"{key}: expected {expected_sha256}, S3 has {actual}")


def upload_raw(
    client,
    bucket: str,
    path: Path,
    manifest: Manifest,
    *,
    source: str,
    dry_run: bool = False,
    root: str = "raw",
) -> str:
    """Upload a file and its manifest, then read the file back and check its SHA-256.

    Returns the file's S3 key. With dry_run nothing is written. Real data always uses
    root="raw"; the smoke script uses root="smoke".
    """
    path = Path(path)
    if path.stat().st_size != manifest.size_bytes or sha256_file(path) != manifest.sha256:
        raise ChecksumMismatchError(f"{path.name} does not match its manifest")
    key = raw_key(source, manifest.version, manifest.retrieval_date, path.name, root)
    for target in (key, manifest_key(key)):
        if key_exists(client, bucket, target):
            raise AlreadyExistsError(target)
    if dry_run:
        return key
    if manifest.size_bytes > MAX_PUT_BYTES:
        raise ValueError(f"{path.name} is too large for a single upload (multipart not built yet)")
    with path.open("rb") as body:
        _put(client, bucket, key, body, manifest.sha256)
    verify_object(client, bucket, key, manifest.sha256)
    _put(client, bucket, manifest_key(key), manifest.to_json().encode())
    return key


def _list_keys(client, bucket: str, prefix: str):
    token = None
    while True:
        args = {"Bucket": bucket, "Prefix": prefix}
        if token:
            args["ContinuationToken"] = token
        page = client.list_objects_v2(**args)
        yield from page.get("Contents", [])
        if not page.get("IsTruncated"):
            return
        token = page["NextContinuationToken"]


def verify_all(client, bucket: str, prefix: str = "raw/") -> list[str]:
    """Check every raw object against its manifest. Returns a list of problems."""
    objects = {item["Key"]: item["Size"] for item in _list_keys(client, bucket, prefix)}
    problems = []
    for key, size in sorted(objects.items()):
        if key.endswith(MANIFEST_SUFFIX):
            if key[: -len(MANIFEST_SUFFIX)] not in objects:
                problems.append(f"{key}: manifest without a data file")
            continue
        if manifest_key(key) not in objects:
            problems.append(f"{key}: no manifest")
            continue
        text = client.get_object(Bucket=bucket, Key=manifest_key(key))["Body"].read().decode()
        try:
            manifest = Manifest.from_json(text)
        except (ValueError, TypeError) as err:
            problems.append(f"{manifest_key(key)}: unreadable manifest ({err})")
            continue
        if size != manifest.size_bytes:
            problems.append(f"{key}: size {size} but manifest says {manifest.size_bytes}")
        elif sha256_object(client, bucket, key) != manifest.sha256:
            problems.append(f"{key}: checksum differs from the manifest")
    return problems
