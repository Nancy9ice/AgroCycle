"""Schemas for evidence/methods endpoints and field profile shapes."""
from __future__ import annotations

from typing import Generic, Literal, TypeVar

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

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


class IndicatorGlossaryOut(BaseModel):
    indicator_id: str
    label: str
    formula: str
    aggregation_window: str
    scale: str
    resolution: str
    evidence_type: str
    limitation: str


# --- Field profile shapes ---
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


class ProfileVersionsOut(CamelModel):
    """Which data and rules produced this profile, so a displayed value can be traced."""

    data_version: str
    engine_version: str
    crop_history_period: str
    crop_history_source: str


class FieldProfileOut(CamelModel):
    field_id: str
    versions: ProfileVersionsOut | None = None
    crop_history: SectionOut[CropHistoryOut]
    climate: SectionOut[ClimateOut]
    # No greenness (HLS) features exist yet, so this section is always "not_loaded". Typed as `None`
    # data until the web contract's VegetationProfile has a producer.
    vegetation: SectionOut[None]
    soil: SectionOut[SoilOut]
