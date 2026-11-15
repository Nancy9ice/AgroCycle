"""Schemas for GET /strategies/{id}/transition: the sequence for switching to a longer rotation, from DS2's table."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class TransitionStepOut(BaseModel):
    year: int = Field(description="0 is the step before the rotation starts (manure); 1 and up are the rotation's years.")
    crop: str
    action: str
    needs: list[str]
    timing_note: str
    timing_established: bool = Field(
        description="False when no source gives timing for this step. Almost every step is false: say so, never fill it in."
    )
    evidence_basis: Literal["experimental", "team_proposed", "assumption"]
    source: str
    shows_past_weather: bool = Field(description="True when the field's season-by-season weather bears on this step.")


class ReadinessOut(BaseModel):
    constraint: str
    label: str
    answer: bool | None = Field(description="What the farmer said. None means not answered, never 'no'.")
    status: Literal["yes", "no", "not_answered"]
    step_year: int = Field(description="The step this answer bears on.")


class TransitionOut(BaseModel):
    strategy_id: str
    label: str
    rotation: str
    rules_version: str
    steps: list[TransitionStepOut]
    readiness: list[ReadinessOut] | None = Field(
        description="From the farmer's answers in a saved comparison; None when no analysis was given."
    )
    caveats: list[str]
    data_version: str
