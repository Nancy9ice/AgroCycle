"""Schemas for compare and analyses endpoints."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, StrictBool

from api.schemas.fields import FieldOut

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


class ContextAnswers(BaseModel):
    """Farm context the form collects that no rule reads yet.

    Recorded, echoed back and shown to the adviser, but it never changes the outcome. `null` means unknown.
    """

    model_config = ConfigDict(extra="forbid")

    hay_equipment_or_contractor: StrictBool | None = Field(
        default=None, description="Equipment, or a contractor, to cut and bale hay."
    )
    storage_space: StrictBool | None = Field(default=None, description="Space to store hay or grain.")
    extra_labour: Literal["little", "some", "plenty"] | None = Field(
        default=None, description="Extra help at busy times."
    )


CONTEXT_NOTE = (
    "Hay equipment, storage space and extra labour are recorded for you and your adviser. "
    "They do not change the result, because no rule uses them yet."
)


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
    context: ContextAnswers = Field(
        default_factory=ContextAnswers,
        description="Context-only answers: stored and shown, but no rule reads them, so the outcome is unchanged.",
    )
    sample_indicators: StrictBool = Field(
        default=False,
        description="Demo only: pretend the four required indicators are known and fine. "
        "The response says `preview: true`.",
    )


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
    context_recorded: ContextAnswers = Field(default_factory=ContextAnswers)
    context_note: str = CONTEXT_NOTE
    persistence: Literal["stored", "temporary", "failed"] = Field(
        default="stored",
        description=(
            "stored: saved, and GET /analyses/{id} will return it. temporary: saved in memory only, lost when "
            "the server restarts. failed: not saved, so the share link will not work."
        ),
    )
    persistence_warning: str | None = Field(
        default=None, description="Plain-language explanation when persistence is not 'stored'."
    )
