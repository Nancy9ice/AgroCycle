"""Live: the catalog covers everything in S3 under raw/, and each pull's recount matches the scan.
Skipped without S3 access (only DS1 and DS2 have it besides the DE)."""
import pytest

from transform.sources.catalog import SOURCES
from transform.sources.scan import MANIFEST_SUFFIX, scan_pull


@pytest.fixture(scope="module")
def s3():
    try:
        from common.config import s3_bucket, s3_client

        client, bucket = s3_client(), s3_bucket()
        client.list_objects_v2(Bucket=bucket, Prefix="raw/", MaxKeys=1)
    except Exception as error:  # noqa: BLE001 - any failure to reach S3 means skip
        pytest.skip(f"no usable S3 access: {error}")
    return client, bucket


def test_every_object_under_raw_belongs_to_exactly_one_source(s3):
    client, bucket = s3
    uncovered, multiple = [], []
    for page in client.get_paginator("list_objects_v2").paginate(Bucket=bucket, Prefix="raw/"):
        for obj in page.get("Contents", []):
            hits = [sid for sid, rec in SOURCES.items() if obj["Key"].startswith(rec["prefix"])]
            if not hits:
                uncovered.append(obj["Key"])
            elif len(hits) > 1:
                multiple.append(obj["Key"])
    assert not uncovered, f"{len(uncovered)} objects under no source, e.g. {uncovered[:3]}"
    assert not multiple


def test_scan_counts_equal_an_independent_listing_for_the_small_pulls(s3):
    client, bucket = s3
    for sid in ("cdl", "marsden_supplement", "marsden_europepmc", "hls_no_data", "ssurgo"):
        prefix = SOURCES[sid]["prefix"]
        keys = [o for p in client.get_paginator("list_objects_v2").paginate(Bucket=bucket, Prefix=prefix)
                for o in p.get("Contents", [])]
        data = [o for o in keys if not o["Key"].endswith(MANIFEST_SUFFIX)]
        scan = scan_pull(client, bucket, prefix)
        assert (scan["file_count"], scan["total_bytes"]) == (len(data), sum(o["Size"] for o in data)), sid
