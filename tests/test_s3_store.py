import base64

import pytest
from botocore.exceptions import ClientError

from ingest.manifest import build_manifest
from ingest.s3_store import (
    AlreadyExistsError,
    ChecksumMismatchError,
    key_exists,
    manifest_key,
    raw_key,
    upload_raw,
    verify_all,
)

FIELDS = {
    "source_url": "https://example.org/data.csv",
    "product": "Test product",
    "version": "v1",
    "retrieval_date": "2026-11-14",
    "licence": "public domain",
    "subset": {"kind": "bbox"},
    "evidence_type": "observed",
    "scale": "grid",
}


class _Body:
    def __init__(self, data):
        self.data = data

    def read(self):
        return self.data

    def iter_chunks(self, chunk_size=1 << 20):
        for i in range(0, len(self.data), chunk_size):
            yield self.data[i : i + chunk_size]


def _error(code, operation):
    return ClientError({"Error": {"Code": code, "Message": code}}, operation)


class FakeS3:
    """The few S3 calls the store uses, with the same errors as the real service."""

    def __init__(self, corrupt_uploads=False):
        self.objects = {}
        self.corrupt_uploads = corrupt_uploads

    def head_object(self, Bucket, Key):
        if Key not in self.objects:
            raise _error("404", "HeadObject")
        return {"ContentLength": len(self.objects[Key])}

    def put_object(self, Bucket, Key, Body, IfNoneMatch=None, ChecksumSHA256=None):
        if IfNoneMatch == "*" and Key in self.objects:
            raise _error("PreconditionFailed", "PutObject")
        data = Body if isinstance(Body, bytes) else Body.read()
        if ChecksumSHA256:
            import hashlib

            if base64.b64decode(ChecksumSHA256) != hashlib.sha256(data).digest():
                raise _error("BadDigest", "PutObject")
        if self.corrupt_uploads and not Key.endswith(".manifest.json"):
            data = data[:-1] + b"X"
        self.objects[Key] = data

    def get_object(self, Bucket, Key):
        return {"Body": _Body(self.objects[Key])}

    def list_objects_v2(self, Bucket, Prefix="", ContinuationToken=None):
        keys = sorted(k for k in self.objects if k.startswith(Prefix))
        return {"Contents": [{"Key": k, "Size": len(self.objects[k])} for k in keys]}


@pytest.fixture
def data_file(tmp_path):
    path = tmp_path / "data.csv"
    path.write_bytes(b"a,b\n1,2\n")
    return path


def test_upload_writes_file_and_manifest_under_the_raw_layout(data_file):
    client = FakeS3()
    key = upload_raw(client, "bkt", data_file, build_manifest(data_file, **FIELDS), source="power")
    assert key == raw_key("power", "v1", "2026-11-14", "data.csv")
    assert set(client.objects) == {key, manifest_key(key)}
    assert verify_all(client, "bkt") == []


def test_second_upload_to_the_same_key_is_refused(data_file):
    client = FakeS3()
    manifest = build_manifest(data_file, **FIELDS)
    upload_raw(client, "bkt", data_file, manifest, source="power")
    with pytest.raises(AlreadyExistsError):
        upload_raw(client, "bkt", data_file, manifest, source="power")


def test_s3_conditional_write_also_blocks_overwrites(data_file):
    from ingest.s3_store import _put

    client = FakeS3()
    _put(client, "bkt", "raw/x", b"one")
    with pytest.raises(AlreadyExistsError):
        _put(client, "bkt", "raw/x", b"two")
    assert client.objects["raw/x"] == b"one"


def test_dry_run_writes_nothing(data_file):
    client = FakeS3()
    key = upload_raw(
        client, "bkt", data_file, build_manifest(data_file, **FIELDS), source="power", dry_run=True
    )
    assert key.startswith("raw/power/") and client.objects == {}


def test_file_changed_after_its_manifest_was_built_is_not_uploaded(data_file):
    client = FakeS3()
    manifest = build_manifest(data_file, **FIELDS)
    data_file.write_bytes(b"a,b\n9,9\n")
    with pytest.raises(ChecksumMismatchError):
        upload_raw(client, "bkt", data_file, manifest, source="power")
    assert client.objects == {}


def test_corrupted_upload_is_detected_and_no_manifest_is_written(data_file):
    client = FakeS3(corrupt_uploads=True)
    with pytest.raises(ChecksumMismatchError):
        upload_raw(client, "bkt", data_file, build_manifest(data_file, **FIELDS), source="power")
    assert not any(k.endswith(".manifest.json") for k in client.objects)


def test_verify_all_reports_tampering_and_missing_manifests(data_file):
    client = FakeS3()
    key = upload_raw(client, "bkt", data_file, build_manifest(data_file, **FIELDS), source="power")
    client.objects[key] = b"a,b\n1,3\n"  # same size, different content
    client.objects["raw/power/v1/2026-11-14/orphan.csv"] = b"x"
    problems = verify_all(client, "bkt")
    assert any("checksum differs" in p for p in problems)
    assert any("orphan.csv: no manifest" in p for p in problems)


def test_key_exists_raises_a_clear_error_on_403():
    class Forbidden(FakeS3):
        def head_object(self, Bucket, Key):
            raise _error("403", "HeadObject")

    with pytest.raises(PermissionError, match="s3:ListBucket"):
        key_exists(Forbidden(), "bkt", "raw/x")
