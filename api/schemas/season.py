"""Schemas for GET /fields/{id}/season-summary: past weather exposure per season, from DS2's field indicators."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class SeasonValueOut(BaseModel):
    year: int
    value: float | None = Field(description="None when the season is unknown; it is never read as zero.")
    status: str
    window_start: str
    window_end: str
    unknown_reason: str = ""


class SeasonExtremeOut(BaseModel):
    year: int
    value: float


class SeasonThresholdOut(BaseModel):
    """What an indicator counts and the threshold behind it, from DS2's season_stress_thresholds table."""

    what_it_counts: str
    threshold: str = Field(description='The line a count is made against, e.g. ">= 30"; "none" for a mean or a total.')
    unit: str
    evidence_basis: Literal["experimental", "team_proposed", "assumption"]
    review: Literal["not_expert_reviewed", "expert_reviewed"]
    limitation: str
    code_version: str


class SeasonIndicatorOut(BaseModel):
    indicator_id: str
    label: str
    unit: str
    evidence_type: str
    scale: str = Field(description="'grid': a ~50 km weather-model cell, not a measurement at the field.")
    source: str
    formula: str
    limitation: str
    threshold: SeasonThresholdOut | None = Field(
        default=None, description="DS2's threshold record for this indicator; None if the table is not loaded."
    )
    seasons: list[SeasonValueOut]
    seasons_used: int
    seasons_total: int
    highest: SeasonExtremeOut | None = Field(description="The season with the largest value (earliest if tied).")
    lowest: SeasonExtremeOut | None = Field(description="The season with the smallest value (earliest if tied).")


class SeasonSummaryOut(BaseModel):
    field_id: str
    period: str
    indicators: list[SeasonIndicatorOut]
    caveats: list[str]
    data_version: str
