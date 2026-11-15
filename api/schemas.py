"""Backward-compatibility shim — the real schemas live in api/schemas/ package.
Python loads the package (api/schemas/__init__.py) in preference to this file."""
from __future__ import annotations

from typing import Generic, Literal, TypeVar

from pydantic import BaseModel, ConfigDict, Field, StrictBool
from pydantic.alias_generators import to_camel

PriorityId = Literal["soil", "water", "inputs", "income", "forage"]

EvidenceType = Literal[
    "observed",
    "derived",
    "classified",
    "survey",
    "model_reanalysis",
    "experimental",
    "published",
    "assumption",
]


class CompareRequest(BaseModel):
    """What the farmer told us. `null` or omitted means unknown, and is never read as `false`."""

    model_config = ConfigDict(extra="forbid")

    # StrictBool: pydantic's default would turn "yes", "true" or 1 into True. An answer is true, false or
    # null, nothing else, so anything else is rejected rather than interpreted.
    manure_access: StrictBool | None = None
    forage_use_or_buyer: StrictBool | None = None
    oat_use_or_buyer: StrictBool | None = None
    small_grain_equipment_or_contractor: StrictBool | None = None
    priorities: list[PriorityId] = Field(default_factory=list, description='Priorities marked "high".')
    sample_indicators: StrictBool = Field(
        default=False,
        description="Demo only: pretend the four required indicators are known and fine. "
        "The response says `preview: true`.",
    )


class FieldOut(BaseModel):
    field_id: str
    county: str
    boundary_source: Literal["demo", "real"]
    role: Literal["primary", "test"]
    field_class: str | None


class RuleFindingOut(BaseModel):
    rule_id: str
    target: str
    effect: Literal["in_domain", "qualified", "out_of_domain", "abstain_outcome"]
    condition_text: str
    rationale: str
    review: Literal["not_expert_reviewed", "expert_reviewed"]


class OutcomeAssessmentOut(BaseModel):
    outcome_id: str
    label: str
    status: Literal["in_domain", "qualified", "abstained", "out_of_domain", "not_assessed"]
    claimable: bool
    evidence_type: EvidenceType | None
    source: str | None
    statement: str | None
    caution: str
    caution_reference: str
    findings: list[RuleFindingOut]


class StrategyAssessmentOut(BaseModel):
    strategy_id: Literal["A", "B", "C"]
    label: str
    rotation: str
    feasibility: Literal["available", "qualified", "unavailable"]
    operational_requirements: list[str]
    findings: list[RuleFindingOut]


class ConstraintsRecordedOut(BaseModel):
    manure_access: bool | None
    forage_use_or_buyer: bool | None
    oat_use_or_buyer: bool | None
    small_grain_equipment_or_contractor: bool | None


class DecisionOut(BaseModel):
    field_id: str
    boundary_source: str
    crop_history_summary: str
    outcome: Literal["strategy_worth_exploring", "qualified_comparison", "abstention"]
    outcome_reason: str
    strategies: list[StrategyAssessmentOut]
    outcomes: list[OutcomeAssessmentOut]
    unknowns: list[str]
    constraints_recorded: ConstraintsRecordedOut
    priorities_recorded: list[str]
    rules_version: str
    limitations: list[str]


class CompareResponse(BaseModel):
    field: FieldOut
    decision: DecisionOut
    preview: bool = Field(description="True when sample indicator values were used. Not a real result.")
    analysis_id: str | None = None
    created_at: str | None = None
    engine_version: str = ""
    data_version: str = ""


class HealthOut(BaseModel):
    status: Literal["ok", "degraded"]
    data_source: str
    rules_version: str
    clickhouse: bool = False
    data_version: str = ""


# --- Demo fields (GET /fields/demo) ---
class SourceCoverageOut(BaseModel):
    source_id: str
    status: Literal["available", "partial", "unavailable", "not_assessed"]
    note: str = ""


class DemoFieldOut(BaseModel):
    field_id: str
    county: str
    role: Literal["primary", "test"]
    boundary_source: Literal["demo", "real"]
    is_demo: bool
    area_ha: float
    geometry: dict  # GeoJSON geometry object


# --- Field validation (POST /fields) ---
class FieldInputRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    demo_field_id: str | None = None
    geometry: dict | None = None
    name: str | None = Field(None, max_length=60)
    boundary_source: Literal["demo", "farmer_provided", "drawn"] = "drawn"


class ValidationError(BaseModel):
    code: str
    message: str


class FieldValidationOut(BaseModel):
    field_id: str
    valid: bool
    errors: list[ValidationError]
    name: str | None
    county: str | None
    area_ha: float | None
    boundary_source: str
    role: str | None
    is_demo: bool
    in_pilot_area: bool
    is_preprocessed: bool
    coverage: list[SourceCoverageOut]
    data_version: str


# --- Timeseries (GET /fields/{id}/timeseries) ---
class TimeSeriesPointOut(BaseModel):
    date: str
    variable: str
    value: float | None
    unit: str
    obs: int


class TimeSeriesOut(BaseModel):
    field_id: str
    kind: str
    from_date: str
    to_date: str
    max_points: int
    points: list[TimeSeriesPointOut]
    data_version: str


# --- Constraint options (GET /meta/constraint-options) ---
class ConstraintChoiceOut(BaseModel):
    value: str
    label: str


class ConstraintQuestionOut(BaseModel):
    field: str
    group: Literal["priorities", "constraints", "context"]
    label: str
    input_type: Literal["single_choice", "multi_select", "text", "three_level"]
    choices: list[ConstraintChoiceOut]
    help_text: str
    affects: str


class MetaConstraintOptionsOut(BaseModel):
    questions: list[ConstraintQuestionOut]


# --- Marsden evidence (GET /evidence/marsden) ---
class MarsdenRowOut(BaseModel):
    rotation: str
    metric: str
    value: float
    unit: str
    evidence_type: str
    source_id: str


class MarsdenEvidenceOut(BaseModel):
    title: str
    description: str
    rows: list[MarsdenRowOut]
    caveats: list[str]
    reference: str
    data_version: str


# --- Lineage (GET /lineage/{indicator_id}) ---
class LineageOut(BaseModel):
    indicator_id: str
    label: str
    source_ids: list[str]
    variables: list[str]
    formula: str
    aggregation_window: str
    spatial_support: str
    scale: str
    resolution: str
    evidence_type: str
    missing_data_rule: str
    interpretation: str
    limitation: str
    code_version: str


# --- Sources (GET /sources) ---
class SourceOut(BaseModel):
    source_id: str
    provider: str
    product: str
    product_version: str
    url: str
    spatial_resolution: str
    temporal_resolution: str
    geographic_coverage: str
    historical_coverage: str
    retrieval_date: str
    licence: str
    known_limitations: str
    evidence_type: str
    file_count: int
    total_bytes: int


# --- Indicators glossary (GET /indicators) ---
class IndicatorGlossaryOut(BaseModel):
    indicator_id: str
    label: str
    formula: str
    aggregation_window: str
    scale: str
    resolution: str
    evidence_type: str
    limitation: str


# --- Ask AgroCycle (F1) ---
class AskRequest(BaseModel):
    """Question sent to the AI assistant. `audience` controls plain vs technical language."""

    model_config = ConfigDict(extra="forbid")

    question: str = Field(..., min_length=1, max_length=1000)
    audience: Literal["farmer", "adviser"] = "farmer"


class AskResponse(BaseModel):
    """Grounded answer from the AI assistant.

    `citations` lists indicator IDs from the context that the answer referenced.
    `refused` is true when the question is outside the available context.
    The panel is labelled "AI explanation of AgroCycle's computed results" in the UI.
    """

    answer: str
    citations: list[str]
    refused: bool
    model: str
    log_id: str


# --- Field profile -----------------------------------------------------------------------------------
# The shape of `FieldProfile` in `web/src/features/profile/types.ts`, camelCase on the wire so the web app
# renders it unchanged. The API never returns the status `sample`: that is a frontend-only label.


class CamelModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class TechnicalOut(CamelModel):
    evidence_type: EvidenceType
    scale: str
    indicator_id: str
    variable: str | None = None
    product: str | None = None
    version: str | None = None
    retrieved: str | None = None


class ProvenanceOut(CamelModel):
    title: str
    what_it_is: str
    source: str
    source_url: str | None = None
    precision: str
    gaps: str
    technical: TechnicalOut


class CropYearOut(CamelModel):
    year: int
    code: Literal["C", "S", "G", "A", "H", "O", "L", "X"]


class CropHistoryOut(CamelModel):
    years: list[CropYearOut]
    summary: str
    repeated_years: list[int]


class IndicatorOut(CamelModel):
    id: str
    label: str
    value: str
    context: str
    provenance: ProvenanceOut


class ClimateOut(CamelModel):
    period_label: str
    indicators: list[IndicatorOut]


class SoilMeasureOut(CamelModel):
    label: str
    value: str
    # Plain words on what the value covers, e.g. that it is a survey estimate or covers part of the field.
    note: str


class SoilOut(CamelModel):
    series: str
    map_unit: str
    sampling_note: str
    # Measures the soil survey gives for this field. Empty when no indicator outputs are available.
    measures: list[SoilMeasureOut] = Field(default_factory=list)
    not_loaded: list[str]


T = TypeVar("T")


class SectionOut(CamelModel, Generic[T]):
    status: Literal["available", "not_loaded"]
    data: T | None
    provenance: ProvenanceOut | None


class FieldProfileOut(CamelModel):
    field_id: str
    crop_history: SectionOut[CropHistoryOut]
    climate: SectionOut[ClimateOut]
    # No greenness (HLS) features exist yet, so this section is always "not_loaded". Typed as `None`
    # data until the web contract's VegetationProfile has a producer.
    vegetation: SectionOut[None]
    soil: SectionOut[SoilOut]
