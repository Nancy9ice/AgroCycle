"""Request and response models. The response mirrors the engine's `Decision` field for field, so the
OpenAPI schema is the contract the frontend renders (`web/src/features/compare/types.ts`)."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, StrictBool

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


class HealthOut(BaseModel):
    status: Literal["ok"]
    data_source: str
    rules_version: str


# --- Field profile -----------------------------------------------------------------------------------
# The shape of `FieldProfile` in `web/src/features/profile/types.ts`, camelCase on the wire so the web app
# renders it unchanged. The API never returns the status `sample`: that is a frontend-only label.

from typing import Generic, TypeVar

from pydantic.alias_generators import to_camel


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


class SoilOut(CamelModel):
    series: str
    map_unit: str
    sampling_note: str
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
