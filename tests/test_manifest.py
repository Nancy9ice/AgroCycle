import hashlib

import pytest

from ingest.manifest import Manifest, build_manifest, sha256_file

FIELDS = {
    "source_url": "https://example.org/data.csv",
    "product": "Test product",
    "version": "v1",
    "retrieval_date": "2026-11-14",
    "licence": "public domain",
    "subset": {"kind": "bbox", "bbox": [-93.7, 42.0, -93.5, 42.1]},
    "evidence_type": "observed",
    "scale": "30 m raster",
}


def test_sha256_file_matches_hashlib(tmp_path):
    path = tmp_path / "a.bin"
    path.write_bytes(b"abc" * 1_000_000)  # larger than one read chunk
    assert sha256_file(path) == hashlib.sha256(b"abc" * 1_000_000).hexdigest()


def test_build_manifest_records_hash_and_size(tmp_path):
    path = tmp_path / "a.txt"
    path.write_bytes(b"abc")
    manifest = build_manifest(path, **FIELDS)
    assert manifest.sha256 == hashlib.sha256(b"abc").hexdigest()
    assert manifest.size_bytes == 3


def test_manifest_round_trips_through_json(tmp_path):
    path = tmp_path / "a.txt"
    path.write_bytes(b"abc")
    manifest = build_manifest(path, notes="resampled", **FIELDS)
    assert Manifest.from_json(manifest.to_json()) == manifest


@pytest.mark.parametrize(
    "change",
    [
        {"evidence_type": "guess"},
        {"retrieval_date": "14/11/2026"},
        {"retrieval_date": "2026-13-40"},
        {"sha256": "abc"},
        {"size_bytes": -1},
        {"licence": " "},
    ],
)
def test_invalid_manifests_are_rejected(change):
    args = {**FIELDS, "sha256": "0" * 64, "size_bytes": 1, **change}
    with pytest.raises(ValueError):
        Manifest(**args)
