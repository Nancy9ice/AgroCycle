"""Schemas for GET /fields/{id}/cover-calendar: what satellite images say about cover, month by month."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

CoverState = Literal["bare", "likely_bare", "green", "unknown"]


class CoverMonthOut(BaseModel):
    month: int = Field(ge=1, le=12)
    state: CoverState
    usable_images: int = Field(description="Images that month with at least half the field clear of cloud.")
    bare_days: int = Field(description="Days of the month inside a bare window.")
    days: int


class CoverYearOut(BaseModel):
    year: int
    months: list[CoverMonthOut]
    bare_months: int = Field(description="Months that are bare or likely bare.")
    months_with_images: int = Field(description="Months with enough usable images to say green or bare.")


class BareWindowOut(BaseModel):
    start: str
    end: str
    bare_days: int
    confidence: str
    seen_in_images: bool = Field(description="False when the window crosses months that have no usable image.")


class CoverCalendarOut(BaseModel):
    field_id: str
    source: str
    evidence_type: str
    scale: str
    ndvi_threshold: float
    min_bare_days: int
    years: list[CoverYearOut]
    bare_windows: list[BareWindowOut]
    legend: dict[str, str]
    caveats: list[str]
    data_version: str
