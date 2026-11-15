"""Build data_sources and source_links. Dry run unless --load.

    python -m transform.sources.run            # scan S3, build, validate, print
    python -m transform.sources.run --load     # also load both tables (the user's say-so)
"""
from __future__ import annotations

import argparse
import json

import pandas as pd

from common.schemas import DATA_SOURCES, SOURCE_LINKS

from .catalog import COMPILED_FROM, LINEAGE_TEXT_TO_SOURCES, SOURCES, TABLE_SOURCES
from .scan import scan_pull


class SourceBuildError(RuntimeError):
    pass


def build_sources(scans: dict[str, dict]) -> pd.DataFrame:
    """One row per catalog source. `scans` maps source_id to scan_pull's result."""
    rows = []
    for source_id, record in SOURCES.items():
        if source_id not in scans:
            raise SourceBuildError(f"no scan for source {source_id}")
        scan = scans[source_id]
        flags = record["quality_flags"] + ("; " + "; ".join(scan["notes"]) if scan["notes"] else "")
        rows.append({
            "source_id": source_id,
            "provider": record["provider"],
            "product": scan["product"],
            "product_version": record["product_version"],
            "url": record["url"],
            "variables": json.dumps(record["variables"]),
            "spatial_resolution": record["spatial_resolution"],
            "temporal_resolution": record["temporal_resolution"],
            "geographic_coverage": record["geographic_coverage"],
            "historical_coverage": record["historical_coverage"],
            "retrieval_date": pd.Timestamp(scan["retrieval_date"]),
            "licence": scan["licence"],
            "processing_steps": record["processing_steps"],
            "quality_flags": flags,
            "known_limitations": record["known_limitations"],
            "evidence_type": scan["evidence_type"],
            "raw_s3_prefix": record["prefix"],
            "file_count": scan["file_count"],
            "total_bytes": scan["total_bytes"],
            "compiled_from": COMPILED_FROM,
        })
    return DATA_SOURCES.validate(pd.DataFrame(rows))


def build_links(lineage: pd.DataFrame, source_ids: set[str]) -> pd.DataFrame:
    """Indicator links from the lineage's source text, plus the table links. Unknown text fails."""
    rows = []
    for _, r in lineage.iterrows():
        names = json.loads(r["source_ids"])
        for name in names:
            if name not in LINEAGE_TEXT_TO_SOURCES:
                raise SourceBuildError(f"indicator {r['indicator_id']}: source text not in the catalog: {name!r}")
            rows += [("indicator", r["indicator_id"], sid) for sid in LINEAGE_TEXT_TO_SOURCES[name]]
        if not names:
            raise SourceBuildError(f"indicator {r['indicator_id']} names no source")
    rows += [("table", table, sid) for table, sids in TABLE_SOURCES.items() for sid in sids]
    unknown = {sid for _, _, sid in rows} - source_ids
    if unknown:
        raise SourceBuildError(f"links to sources that do not exist: {sorted(unknown)}")
    frame = pd.DataFrame(rows, columns=["subject_type", "subject_id", "source_id"]).drop_duplicates()
    return SOURCE_LINKS.validate(frame.reset_index(drop=True))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--load", action="store_true", help="write to ClickHouse (default: dry run)")
    args = ap.parse_args(argv)

    from common.config import clickhouse_client, s3_bucket, s3_client
    from common.load import load

    s3, bucket = s3_client(), s3_bucket()
    scans = {sid: scan_pull(s3, bucket, rec["prefix"]) for sid, rec in SOURCES.items()}
    sources = build_sources(scans)
    ch = clickhouse_client()
    lineage = pd.DataFrame(ch.query("SELECT DISTINCT indicator_id, source_ids FROM indicator_lineage").result_rows,
                           columns=["indicator_id", "source_ids"])
    links = build_links(lineage, set(sources["source_id"]))
    print(sources[["source_id", "evidence_type", "retrieval_date", "file_count", "total_bytes"]].to_string(index=False))
    print(f"{len(links)} links ({(links.subject_type == 'indicator').sum()} indicator, "
          f"{(links.subject_type == 'table').sum()} table)")
    if not args.load:
        print("dry run: nothing written (use --load)")
        return 0
    for name, frame in (("data_sources", sources), ("source_links", links)):
        result = load(ch, name, frame)
        print(name, result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
