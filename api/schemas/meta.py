"""Schemas for health and meta endpoints."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class CountyOutlineOut(BaseModel):
    county: str
    ring: list[list[float]] = Field(description="Closed ring of [longitude, latitude] points.")


class PilotAreaOut(BaseModel):
    description: str
    counties: list[CountyOutlineOut]


class HealthOut(BaseModel):
    status: Literal["ok", "degraded"]
    data_source: str
    rules_version: str
    clickhouse: bool = False
    data_version: str = ""


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
