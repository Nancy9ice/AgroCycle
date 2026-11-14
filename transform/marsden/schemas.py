"""Pandera schemas for the Marsden reproduction outputs (AgroCycle, DS2, roadmap Phase 6).

The DE's half of Phase 6 is validating these records before they are loaded. These are the schemas for the
two tables the load reads, plus the reconciliation and lineage records kept as evidence. They follow the
house pattern in ``transform/field_schema.py``: validate lazily, return findings as strings, and let the
caller decide whether to stop.

``marsden_repro.run`` validates with these before writing, so a reproduction that drifts out of range fails
rather than quietly writing a bad table.

Units, as written by the reproduction: nitrogen in kg N/ha/yr, herbicide in kg active ingredient/ha/yr.
"""
from __future__ import annotations

import pandas as pd
import pandera.pandas as pa

ROTATIONS = ["2-yr", "3-yr", "4-yr"]
FIRST_YEAR = 2003
LAST_YEAR = 2011
SEASONS = LAST_YEAR - FIRST_YEAR + 1
RECONCILIATION_STATUSES = ["MATCH", "WITHIN_SEM", "UNRECONCILED", "INFO"]

# Generous upper bounds: these reject a unit error or a parsing slip, not an unexpected but real value.
MAX_N_KG_HA = 300.0
MAX_HERBICIDE_KG_HA = 20.0
SUM_TOLERANCE = 1e-6

EVIDENCE_TYPES = [
    "observed",
    "derived",
    "classified",
    "survey",
    "model_reanalysis",
    "experimental",
    "published",
    "assumption",
]
LINEAGE_FIELDS = (
    "indicator_id",
    "variables",
    "formula",
    "unit",
    "source",
    "source_url",
    "product_version",
    "spatial_scale",
    "temporal_window",
    "missing_data_rule",
    "evidence_type",
    "limitation",
)


def _nitrogen_column(nullable: bool = False) -> pa.Column:
    return pa.Column(
        float,
        pa.Check.in_range(0.0, MAX_N_KG_HA),
        nullable=nullable,
        description="kg N/ha/yr, rotation-area weighted",
    )


def _applied_n_matches_components(frame: pd.DataFrame) -> bool:
    return bool(
        ((frame["manufactured_n"] + frame["manure_n"] - frame["applied_n"]).abs() <= SUM_TOLERANCE).all()
    )


management_by_year_schema = pa.DataFrameSchema(
    {
        "rotation": pa.Column(str, pa.Check.isin(ROTATIONS), nullable=False),
        "year": pa.Column(int, pa.Check.in_range(FIRST_YEAR, LAST_YEAR), nullable=False),
        "manufactured_n": _nitrogen_column(),
        "manure_n": _nitrogen_column(),
        "applied_n": _nitrogen_column(),
        "herbicide": pa.Column(
            float,
            pa.Check.in_range(0.0, MAX_HERBICIDE_KG_HA),
            nullable=False,
            description="kg active ingredient/ha/yr",
        ),
    },
    checks=[
        pa.Check(_applied_n_matches_components, error="applied_n must equal manufactured_n + manure_n"),
        pa.Check(
            lambda frame: not frame.duplicated(subset=["rotation", "year"]).any(),
            error="one row per rotation and year",
        ),
        pa.Check(
            lambda frame: frame.groupby("rotation")["year"].count().eq(SEASONS).all(),
            error=f"every rotation needs {SEASONS} seasons",
        ),
    ],
    strict=False,
    coerce=False,
)

management_summary_schema = pa.DataFrameSchema(
    {
        "rotation": pa.Column(str, pa.Check.isin(ROTATIONS), unique=True, nullable=False),
        "manufactured_n": _nitrogen_column(),
        "manure_n": _nitrogen_column(),
        "applied_n": _nitrogen_column(),
        "herbicide": pa.Column(float, pa.Check.in_range(0.0, MAX_HERBICIDE_KG_HA), nullable=False),
        "n_years": pa.Column(int, pa.Check.eq(SEASONS), nullable=False),
    },
    checks=[
        pa.Check(_applied_n_matches_components, error="applied_n must equal manufactured_n + manure_n"),
        pa.Check(
            lambda frame: len(frame) == len(ROTATIONS),
            error=f"one row per rotation ({len(ROTATIONS)})",
        ),
    ],
    strict=False,
    coerce=False,
)

reconciliation_schema = pa.DataFrameSchema(
    {
        "quantity": pa.Column(str, nullable=False),
        "rotation": pa.Column(str, nullable=False),
        "computed": pa.Column(float, nullable=False),
        "reference": pa.Column(float, nullable=False),
        "source": pa.Column(str, pa.Check.str_length(min_value=1), nullable=False),
        "rule": pa.Column(str, pa.Check.str_length(min_value=1), nullable=False),
        "status": pa.Column(str, pa.Check.isin(RECONCILIATION_STATUSES), nullable=False),
        "note": pa.Column(nullable=True),
    },
    strict=False,
    coerce=False,
)


def _schema_findings(schema: pa.DataFrameSchema, frame: pd.DataFrame, name: str) -> list[str]:
    missing = [
        column
        for column, spec in schema.columns.items()
        if spec.required and column not in frame.columns
    ]
    if missing:
        return [f"{name}: missing column(s) {', '.join(missing)}"]
    try:
        schema.validate(frame, lazy=True)
    except pa.errors.SchemaErrors as err:
        return [
            f"{name}: {row.column or 'table'} failed {row.check}"
            for row in err.failure_cases.drop_duplicates(subset=["column", "check"]).itertuples()
        ]
    return []


def lineage_findings(rows: list[dict]) -> list[str]:
    """Check the lineage records that accompany the tables; one complete row per derived indicator."""
    findings = []
    if not rows:
        return ["lineage: no rows"]
    seen = set()
    for row in rows:
        indicator = row.get("indicator_id", "<no indicator_id>")
        empty = [field for field in LINEAGE_FIELDS if not row.get(field)]
        if empty:
            findings.append(f"lineage {indicator}: empty field(s) {', '.join(empty)}")
        if row.get("evidence_type") not in EVIDENCE_TYPES:
            findings.append(f"lineage {indicator}: evidence_type {row.get('evidence_type')!r} not a label")
        if indicator in seen:
            findings.append(f"lineage {indicator}: duplicate indicator_id")
        seen.add(indicator)
    return findings


def validate_outputs(
    by_year: pd.DataFrame,
    summary: pd.DataFrame,
    reconciliation: pd.DataFrame | None = None,
    lineage: list[dict] | None = None,
) -> list[str]:
    """Return every schema finding; an empty list means the outputs are loadable."""
    findings = _schema_findings(management_by_year_schema, by_year, "management_by_year")
    findings += _schema_findings(management_summary_schema, summary, "management_summary")
    if reconciliation is not None:
        findings += _schema_findings(reconciliation_schema, reconciliation, "reconciliation")
    if lineage is not None:
        findings += lineage_findings(lineage)
    return findings
