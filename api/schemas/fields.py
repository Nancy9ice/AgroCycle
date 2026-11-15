"""Schemas for field-related endpoints."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class SourceCoverageOut(BaseModel):
    source_id: str
    status: Literal["available", "partial", "unavailable", "not_assessed"]
    note: str = ""


class DemoFieldOut(BaseModel):
    field_id: str
    county: str
    role: Literal["primary", "test"]
    boundary_source: Literal["demo", "real"]
    is_demo: bool
    area_ha: float
    geometry: dict  # GeoJSON geometry object
    field_class: str | None = Field(
        default=None, description="DS1's classification of the CDL history: rotation, continuous_corn, pasture_hay, mixed."
    )
    domain_note: str = ""
    provenance: str = ""
    cover_detail: str | None = None
    centroid: list[float] = Field(default_factory=list, description="[longitude, latitude]")


class FieldInputRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    demo_field_id: str | None = None
    geometry: dict | None = None
    name: str | None = Field(None, max_length=60)
    boundary_source: Literal["demo", "farmer_provided", "drawn"] = "drawn"


class ValidationError(BaseModel):
    code: str
    message: str


class FieldValidationOut(BaseModel):
    field_id: str
    valid: bool
    errors: list[ValidationError]
    name: str | None
    county: str | None
    area_ha: float | None
    boundary_source: str
    role: str | None
    is_demo: bool
    in_pilot_area: bool
    is_preprocessed: bool
    can_compare: bool = Field(
        default=False,
        description="True only when the field has pre-processed data. A drawn boundary is validated, not analysed.",
    )
    message: str | None = Field(default=None, description="Plain-language limit to show the user, if any.")
    coverage: list[SourceCoverageOut]
    data_version: str


class FieldOut(BaseModel):
    field_id: str
    county: str
    boundary_source: Literal["demo", "real"]
    role: Literal["primary", "test"]
    field_class: str | None


class TimeSeriesPointOut(BaseModel):
    date: str
    variable: str
    value: float | None
    unit: str
    obs: int


class TimeSeriesOut(BaseModel):
    field_id: str
    kind: str
    from_date: str
    to_date: str
    max_points: int
    points: list[TimeSeriesPointOut]
    data_version: str
