"""Schemas for GET /fields/{id}/season-summary: past weather exposure per season, from DS2's field indicators."""
from __future__ import annotations

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


class SeasonIndicatorOut(BaseModel):
    indicator_id: str
    label: str
    unit: str
    evidence_type: str
    scale: str = Field(description="'grid': a ~50 km weather-model cell, not a measurement at the field.")
    source: str
    formula: str
    limitation: str
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
