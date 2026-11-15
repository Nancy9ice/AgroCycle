"""data_sources and source_links: catalog completeness, scan rules, link rules. Offline."""
import json

import pandas as pd
import pytest

from transform.sources import run as R
from transform.sources.catalog import LINEAGE_TEXT_TO_SOURCES, SOURCES, TABLE_SOURCES
from transform.sources.scan import ScanError, scan_pull

REQUIRED = ("provider", "product_version", "url", "variables", "spatial_resolution", "temporal_resolution",
            "geographic_coverage", "historical_coverage", "processing_steps", "quality_flags", "known_limitations")


def fake_scan(**over):
    base = {"file_count": 3, "total_bytes": 10, "notes": [], "product": "A product", "licence": "A licence",
            "evidence_type": "observed", "retrieval_date": "2026-11-14"}
    return {**base, **over}


def all_scans():
    return {sid: fake_scan(retrieval_date=rec["prefix"].rstrip("/").rsplit("/", 1)[1]) for sid, rec in SOURCES.items()}


def test_every_catalog_record_has_every_prd_field():
    for sid, rec in SOURCES.items():
        for name in REQUIRED:
            assert rec[name], f"{sid}.{name} is empty"
        assert rec["prefix"].startswith("raw/") and rec["prefix"].endswith("/")
        assert isinstance(rec["variables"], list) and rec["variables"]


def test_prefixes_are_distinct_and_do_not_nest():
    prefixes = [r["prefix"] for r in SOURCES.values()]
    assert len(set(prefixes)) == len(prefixes)
    assert not any(a != b and b.startswith(a) for a in prefixes for b in prefixes)


def test_build_gives_one_valid_row_per_source():
    frame = R.build_sources(all_scans())
    assert sorted(frame.source_id) == sorted(SOURCES)
    assert json.loads(frame.variables[0])


def test_build_refuses_a_missing_scan():
    scans = all_scans()
    scans.pop("power")
    with pytest.raises(R.SourceBuildError, match="power"):
        R.build_sources(scans)


def test_a_difference_between_manifests_is_kept_in_the_quality_flags():
    scans = all_scans()
    scans["cdl"] = fake_scan(notes=["evidence_type differs between files of this pull: experimental (4); derived (1)"])
    row = R.build_sources(scans).set_index("source_id").loc["cdl"]
    assert "differs between files" in row.quality_flags


def lineage(*pairs):
    return pd.DataFrame([{"indicator_id": i, "source_ids": json.dumps([t])} for i, t in pairs])


def test_every_known_lineage_text_links_to_existing_sources():
    texts = list(LINEAGE_TEXT_TO_SOURCES)
    links = R.build_links(lineage(*[(f"i{n}", t) for n, t in enumerate(texts)]), set(SOURCES))
    assert set(links[links.subject_type == "indicator"].subject_id) == {f"i{n}" for n in range(len(texts))}


def test_an_unknown_lineage_text_fails_and_names_the_indicator():
    with pytest.raises(R.SourceBuildError, match="gdd.*not in the catalog"):
        R.build_links(lineage(("gdd", "Some new source")), set(SOURCES))


def test_an_indicator_with_no_source_fails():
    frame = pd.DataFrame([{"indicator_id": "x", "source_ids": "[]"}])
    with pytest.raises(R.SourceBuildError, match="names no source"):
        R.build_links(frame, set(SOURCES))


def test_a_link_to_a_missing_source_fails():
    with pytest.raises(R.SourceBuildError, match="do not exist"):
        R.build_links(lineage(("gdd", next(iter(LINEAGE_TEXT_TO_SOURCES)))), set(SOURCES) - {"cdl"})


def test_table_links_are_as_specified():
    links = R.build_links(lineage(("gdd", next(iter(LINEAGE_TEXT_TO_SOURCES)))), set(SOURCES))
    tables = links[links.subject_type == "table"].groupby("subject_id").source_id.apply(set).to_dict()
    assert tables == {t: set(s) for t, s in TABLE_SOURCES.items()}
    assert tables["hls_valid_pixels"] == {"hls_l30", "hls_s30", "hls_no_data"}
    assert "fields" not in tables  # boundaries are demo geometry, not a CDL product


class FakeS3:
    def __init__(self, objects, manifests):
        self.objects, self.manifests = objects, manifests

    def get_paginator(self, _):
        outer = self

        class P:
            def paginate(self, Bucket, Prefix):
                yield {"Contents": [{"Key": k, "Size": s} for k, s in outer.objects]}

        return P()

    def get_object(self, Bucket, Key):
        import io
        return {"Body": io.BytesIO(json.dumps(self.manifests[Key]).encode())}


def manifest(**over):
    return {"product": "P", "licence": "L", "evidence_type": "observed", "retrieval_date": "2026-11-14", **over}


def pull(n, manifests):
    objs = [(f"raw/x/{i}", 5) for i in range(n)] + [(f"raw/x/{i}.manifest.json", 1) for i in range(n)]
    return FakeS3(objs, {f"raw/x/{i}.manifest.json": manifests[i] for i in range(n)})


def test_scan_counts_objects_and_bytes_without_the_manifests():
    out = scan_pull(pull(3, [manifest()] * 3), "b", "raw/x/")
    assert (out["file_count"], out["total_bytes"], out["evidence_type"], out["notes"]) == (3, 15, "observed", [])


def test_scan_takes_the_majority_and_notes_the_difference():
    out = scan_pull(pull(3, [manifest(), manifest(), manifest(evidence_type="derived")]), "b", "raw/x/")
    assert out["evidence_type"] == "observed" and "differs" in out["notes"][0]


def test_scan_refuses_a_tie_an_empty_pull_and_a_missing_manifest():
    with pytest.raises(ScanError, match="no majority"):
        scan_pull(pull(2, [manifest(), manifest(licence="other")]), "b", "raw/x/")
    with pytest.raises(ScanError, match="no objects"):
        scan_pull(FakeS3([], {}), "b", "raw/x/")
    with pytest.raises(ScanError, match="manifests"):
        scan_pull(FakeS3([("raw/x/a", 1)], {}), "b", "raw/x/")


def test_scan_refuses_objects_and_manifests_that_do_not_pair_up():
    objs = [("raw/x/a", 1), ("raw/x/b", 1), ("raw/x/a.manifest.json", 1), ("raw/x/a.manifest.json.dup", 1)]
    with pytest.raises(ScanError, match="do not pair up"):
        scan_pull(FakeS3(objs, {}), "b", "raw/x/")
    swapped = [("raw/x/a", 1), ("raw/x/b", 1), ("raw/x/a.manifest.json", 1), ("raw/x/c.manifest.json", 1)]
    with pytest.raises(ScanError, match="do not pair up"):
        scan_pull(FakeS3(swapped, {}), "b", "raw/x/")


def test_scan_names_the_manifest_that_is_bad():
    good = manifest()
    broken = {k: v for k, v in good.items() if k != "licence"}
    with pytest.raises(ScanError, match=r"raw/x/1\.manifest\.json: manifest lacks \['licence'\]"):
        scan_pull(pull(2, [good, broken]), "b", "raw/x/")


def test_build_refuses_a_manifest_date_that_is_not_the_prefix_date():
    scans = all_scans()
    scans["power"] = fake_scan(retrieval_date="2026-01-01")
    with pytest.raises(R.SourceBuildError, match="power.*2026-01-01"):
        R.build_sources(scans)
