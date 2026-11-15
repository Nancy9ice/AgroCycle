"""Schemas for GET /evidence/rules: the decision engine's rule register, read from DS2's engine_* tables."""
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class RuleOut(BaseModel):
    rule_id: str
    applies_to: str = Field(description="An outcome id, 'all_outcomes', or a strategy feasibility target.")
    context_key: str
    operator: str
    value: Any = Field(description="The threshold or set the rule compares against.")
    effect: Literal["in_domain", "qualified", "out_of_domain", "abstain_outcome"]
    condition_text: str
    rationale: str
    evidence_basis: Literal["experimental_context", "team_proposed"]
    review: Literal["not_expert_reviewed", "expert_reviewed"]


class CropClaimOut(BaseModel):
    claim_id: str
    crops: list[str]
    claim: str
    status: Literal["sourced", "research_needed"]
    evidence_type: str
    source: str
    note: str


class OutcomeRuleOut(BaseModel):
    outcome_id: str
    label: str
    claimable: bool = Field(description="False means the engine never makes this claim; it is always 'not assessed'.")
    evidence_type: str
    source: str
    statement: str
    caution: str
    caution_reference: str


class StrategyRuleOut(BaseModel):
    strategy_id: str
    label: str
    rotation: str
    phases: list[str]
    why_included: str
    operational_requirements: list[str]
    evidence_anchor: str


class RegisterSummaryOut(BaseModel):
    rules_total: int
    rules_team_proposed: int
    rules_experimental_context: int
    rules_expert_reviewed: int
    claims_total: int
    claims_sourced: int
    claims_research_needed: int


class RuleRegisterOut(BaseModel):
    rules_version: str = Field(description="The version of the rules loaded in the database.")
    engine_version: str = Field(description="The version of the rules the running engine uses.")
    matches_engine: bool = Field(description="False means the loaded register is stale against the engine.")
    summary: RegisterSummaryOut
    rules: list[RuleOut]
    crop_claims: list[CropClaimOut]
    outcomes: list[OutcomeRuleOut]
    strategies: list[StrategyRuleOut]
    caveats: list[str]
    data_version: str
