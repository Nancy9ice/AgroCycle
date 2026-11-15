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
