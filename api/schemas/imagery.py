"""Schemas for GET /fields/{id}/imagery."""
from __future__ import annotations

from pydantic import BaseModel


class ImageryTileOut(BaseModel):
    tile_id: str
    flight_date: str


class ImageryOut(BaseModel):
    field_id: str
    available: bool
    year: int | None = None
    # One entry per source tile: a field cut from two tiles shows both flight dates.
    tiles: list[ImageryTileOut] = []
    resolution_m: float | None = None
    # West, south, east, north of the picture as drawn, longitude and latitude.
    bounds: list[float] | None = None
    evidence_type: str | None = None
    attribution: str | None = None
    note: str | None = None
