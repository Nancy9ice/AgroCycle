"""Shared FastAPI dependencies extracted from routes."""
from __future__ import annotations

from fastapi import Request

from api.db.repository import FieldRepository
from api.schemas.fields import SourceCoverageOut
from api.settings import Settings

DEMO_COVERAGE = [
    SourceCoverageOut(source_id="cdl", status="available", note="2015–2025, 30 m"),
    SourceCoverageOut(source_id="power", status="available", note="1991–2024, ~50 km grid"),
    SourceCoverageOut(source_id="ssurgo", status="available", note="USDA soil survey"),
    SourceCoverageOut(source_id="hls", status="partial", note="2023–2025, cloud-limited"),
]


def get_repository(request: Request) -> FieldRepository:
    return request.app.state.repository


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


def get_data_version(request: Request) -> str:
    return getattr(request.app.state, "data_version", "unknown")
