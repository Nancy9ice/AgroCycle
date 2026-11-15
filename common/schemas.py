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

_year = pa.Column(int, pa.Check.in_range(1990, 2100), nullable=False)
_pct = pa.Column(float, pa.Check.in_range(0, 100), nullable=False)
_count = pa.Column(int, pa.Check.ge(0), nullable=False)

CROP_CLASS_SHARES = pa.DataFrameSchema(
    {
        "field_id": _key_text,
        "year": _year,
        "cdl_class_code": pa.Column(int, pa.Check.in_range(0, 255), nullable=False),
        "cdl_class_name": _key_text,
        "class_group": _key_text,
        "flag": pa.Column(str, pa.Check.isin(["", "unlisted_code"]), nullable=False),
        "pixels": pa.Column(int, pa.Check.gt(0), nullable=False),
        "share_pct": _pct,
        "resolution_m": pa.Column(int, pa.Check.gt(0), nullable=False),
        "product_version": _key_text,
        "source_s3_key": _key_text,
    },
    unique=["field_id", "year", "cdl_class_code"],
    strict=True,
)

CROP_HISTORY = pa.DataFrameSchema(
    {
        "field_id": _key_text,
        "year": _year,
        "dominant_group": _key_text,
        "status": pa.Column(str, pa.Check.isin(["ok", "mixed_uncertain", "low_confidence"]), nullable=False),
        "dominant_share_pct": _pct,
        "nodata_share_pct": _pct,
        "total_pixels": pa.Column(int, pa.Check.gt(0), nullable=False),
        "rule_version": _key_text,
        "evidence_type": _evidence,
    },
    unique=["field_id", "year"],
    strict=True,
)

CROP_ROTATION = pa.DataFrameSchema(
    {
        "field_id": _key_text,
        "field_class": pa.Column(
            str, pa.Check.isin(["rotation", "continuous_corn", "pasture_hay", "mixed", "other"]), nullable=False
        ),
        "sequence": _key_text,
        "corn_years": _count,
        "soybean_years": _count,
        "pasture_hay_years": _count,
        "alternations": _count,
        "transitions_counted": _count,
        "rule_version": _key_text,
        "evidence_type": _evidence,
        "limitation": _key_text,  # every classification states its limits
    },
    unique=["field_id"],
    strict=True,
)


FIELD_INDICATORS = pa.DataFrameSchema(
    {
        "field_id": _key_text,
        "indicator_id": _key_text,
        "category": pa.Column(
            str, pa.Check.isin(["climate", "soil", "vegetation", "water", "regional", "context"]), nullable=False
        ),
        "value": pa.Column(float, nullable=True),
        "unit": _text,
        "status": pa.Column(
            str, pa.Check.isin(["available", "partial", "unknown", "not_assessed"]), nullable=False
        ),
        "window_start": pa.Column("datetime64[ns]", nullable=True),
        "window_end": pa.Column("datetime64[ns]", nullable=True),
        "valid_obs": pa.Column("Int64", pa.Check.ge(0), nullable=True),
        "unknown_reason": pa.Column(str, nullable=True),
        "run_id": _key_text,
    },
    checks=pa.Check(
        lambda df: ~(df["value"].isna() & (df["status"] == "available")),
        error="a null value cannot be 'available': unknown is not neutral",
    ),
    unique=["field_id", "indicator_id", "window_start"],
    strict=True,
)

SOIL_PROPERTIES = pa.DataFrameSchema(
    {
        "field_id": _key_text,
        "mukey": _text,  # empty for the class rows
        "mu_name": _text,
        "share_pct": pa.Column(float, pa.Check.in_range(0, 100.001), nullable=True),  # float sums can overshoot
        "property": _key_text,
        "value_num": pa.Column(float, nullable=True),
        # empty text is null here: the database key treats the two as one, so the frame must not mix them
        "value_text": pa.Column(str, pa.Check(lambda s: s != "", ignore_na=True), nullable=True),
        "unit": _text,
        "indicator_id": _key_text,
        "run_id": _key_text,
    },
    unique=["field_id", "mukey", "property", "value_text"],
    strict=True,
)

POWER_VARIABLES = ["T2M_MAX", "T2M_MIN", "T2M", "PRECTOTCORR", "RH2M", "ALLSKY_SFC_SW_DWN", "WS2M"]

CLIMATE_POINTS = pa.DataFrameSchema(
    {
        "point_id": _key_text,
        "cell_id": _key_text,
        "latitude": pa.Column(float, pa.Check.in_range(-90, 90), nullable=False),
        "longitude": pa.Column(float, pa.Check.in_range(-180, 180), nullable=False),
        "elevation_m": pa.Column(float, nullable=False),
    },
    unique=["point_id"],
    strict=True,
)

CLIMATE_DAILY = pa.DataFrameSchema(
    {
        "cell_id": _key_text,
        "variable": pa.Column(str, pa.Check.isin(POWER_VARIABLES), nullable=False),
        "date": pa.Column("datetime64[ns]", nullable=False),
        "value": pa.Column(float, nullable=True),
        "unit": _text,
        "qc_flag": pa.Column(
            str, pa.Check.isin(["", "fill", "missing", "null", "soft_t_order", "soft_t_range"]), nullable=False
        ),
    },
    unique=["cell_id", "variable", "date"],
    strict=True,
)


_pixels = pa.Column(int, pa.Check.ge(0), nullable=False)

HLS_VALID_PIXELS = pa.DataFrameSchema(
    {
        "field_id": _key_text,
        "sensor": pa.Column(str, pa.Check.isin(["l30", "s30"]), nullable=False),
        "acquired": pa.Column("datetime64[ns]", nullable=False),
        "sensing_time": pa.Column(str, pa.Check.str_matches(r"^T\d{6}$"), nullable=False),
        "status": pa.Column(str, pa.Check.isin(["observed", "no_data"]), nullable=False),
        "total_pixels": pa.Column(int, pa.Check.gt(0), nullable=False),
        "fill_pixels": _pixels,
        "flagged_pixels": _pixels,
        "valid_pixels": _pixels,
        "valid_share": pa.Column(float, pa.Check.in_range(0, 1), nullable=False),
        "mask_rule": _key_text,
        "source_s3_key": _key_text,
    },
    checks=[
        pa.Check(
            lambda df: df["fill_pixels"] + df["flagged_pixels"] + df["valid_pixels"] == df["total_pixels"],
            error="fill + flagged + valid must equal total: every pixel is exactly one of them",
        ),
        pa.Check(
            lambda df: (df["valid_share"] - df["valid_pixels"] / df["total_pixels"]).abs() < 1e-6,
            error="valid_share must equal valid_pixels / total_pixels",
        ),
        pa.Check(
            lambda df: (df["status"] == "no_data") == (df["fill_pixels"] == df["total_pixels"]),
            error="a window is no_data exactly when every pixel of the field is fill: no observation, never clear",
        ),
    ],
    unique=["field_id", "sensor", "acquired", "sensing_time"],
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
    key_sql: str | None = None  # the key as SQL, when a key column can be null (checked with ifNull)


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
        Table(
            "crop_class_shares", CROP_CLASS_SHARES, ("field_id", "year", "cdl_class_code"), ("field_id",), None
        ),
        Table("crop_history", CROP_HISTORY, ("field_id", "year"), ("field_id",), None),
        Table("crop_rotation", CROP_ROTATION, ("field_id",), ("field_id",), None),
        Table(
            "field_indicators", FIELD_INDICATORS, ("field_id", "indicator_id", "window_start"),
            ("field_id", "indicator_id"), None, lineage_column="indicator_id",
            key_sql="field_id, indicator_id, ifNull(window_start, toDate('1970-01-01'))",
        ),
        Table(
            "soil_properties", SOIL_PROPERTIES, ("field_id", "mukey", "property", "value_text"),
            ("field_id", "property"), None, lineage_column="indicator_id",
            key_sql="field_id, mukey, property, ifNull(value_text, '')",
        ),
        Table("climate_points", CLIMATE_POINTS, ("point_id",), ("point_id",), None),
        Table("climate_daily", CLIMATE_DAILY, ("cell_id", "variable", "date"), ("cell_id", "variable"), None),
        Table(
            "hls_valid_pixels", HLS_VALID_PIXELS, ("field_id", "sensor", "acquired", "sensing_time"),
            ("field_id", "sensor", "sensing_time"), None,
        ),
    )
}
