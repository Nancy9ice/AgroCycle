"""Pandera schemas and the registry of core ClickHouse tables.

A frame is validated here before any insert. The schema lists the columns the caller supplies;
the loader adds `load_id`. `schema/001_core.sql` must name exactly these columns (common.schema_check).
"""

from dataclasses import dataclass

import pandera.pandas as pa

from ingest.manifest import EVIDENCE_TYPES

_text = pa.Column(str, nullable=False)
_key_text = pa.Column(str, pa.Check.str_length(min_value=1), nullable=False)
_evidence = pa.Column(str, pa.Check.isin(EVIDENCE_TYPES), nullable=False)

DATA_SOURCES = pa.DataFrameSchema(
    {
        "source_id": _key_text,
        "s3_key": _key_text,
        "source_url": _key_text,
        "product": _key_text,
        "version": _key_text,
        "retrieval_date": pa.Column(
            "datetime64[ns]",
            pa.Check(lambda s: s == s.dt.normalize(), error="retrieval_date must be a date, with no time of day"),
            nullable=False,
        ),
        "sha256": pa.Column(str, pa.Check.str_matches(r"^[0-9a-f]{64}$"), nullable=False),
        "size_bytes": pa.Column(int, pa.Check.ge(0), nullable=False),
        "licence": _key_text,
        "subset": _text,  # JSON string
        "evidence_type": _evidence,
        "scale": _key_text,
        "notes": _text,
    },
    unique=["source_id", "version", "retrieval_date", "s3_key"],
    strict=True,
)

INDICATOR_LINEAGE = pa.DataFrameSchema(
    {
        "indicator_id": _key_text,
        "label": _text,
        "source_ids": _text,  # JSON string
        "variables": _text,  # JSON string
        "formula": _key_text,
        "aggregation_window": _text,
        "spatial_support": _text,
        "scale": _key_text,
        "resolution": _text,
        "evidence_type": _evidence,
        "missing_data_rule": _key_text,
        "interpretation": _text,
        "limitation": _key_text,  # a lineage row without a stated limitation is not allowed
        "code_version": _key_text,
        "run_id": _key_text,
    },
    unique=["indicator_id", "code_version"],
    strict=True,
)

FIELDS = pa.DataFrameSchema(
    {
        "field_id": _key_text,
        "role": pa.Column(str, pa.Check.isin(["primary", "test"]), nullable=False),
        "boundary_source": pa.Column(str, pa.Check.isin(["demo", "real"]), nullable=False),
        "county": pa.Column(str, pa.Check.isin(["Story", "Boone"]), nullable=False),
        "provenance": _key_text,
        "domain_note": _text,
        "cover_detail": _text,
        "geometry_wkt": _key_text,
    },
    unique=["field_id"],
    strict=True,
)


@dataclass(frozen=True)
class Table:
    name: str
    schema: pa.DataFrameSchema
    key: tuple[str, ...]  # natural key: unique in the table
    text_keys: tuple[str, ...]  # key columns that must not be empty strings
    partition_column: str | None  # None: one partition, the table is reloaded whole
    lineage_column: str | None = None  # set for tables of indicator values: every id needs a lineage row


TABLES = {
    t.name: t
    for t in (
        Table(
            "data_sources",
            DATA_SOURCES,
            ("source_id", "version", "retrieval_date", "s3_key"),
            ("source_id", "version", "s3_key"),
            "source_id",
        ),
        Table(
            "indicator_lineage",
            INDICATOR_LINEAGE,
            ("indicator_id", "code_version"),
            ("indicator_id", "code_version"),
            "code_version",
        ),
        Table("fields", FIELDS, ("field_id",), ("field_id",), None),
    )
}
