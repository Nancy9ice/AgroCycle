"""Schemas for the Ask AgroCycle (F1) endpoints."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class AskRequest(BaseModel):
    """Question sent to the AI assistant. `audience` controls plain vs technical language."""

    model_config = ConfigDict(extra="forbid")

    question: str = Field(..., min_length=1, max_length=1000)
    audience: Literal["farmer", "adviser"] = "farmer"


class AskResponse(BaseModel):
    """Grounded answer from the AI assistant.

    `citations` lists indicator IDs from the context that the answer referenced.
    `refused` is true when the question is outside the available context.
    The panel is labelled "AI explanation of AgroCycle's computed results" in the UI.
    """

    answer: str
    citations: list[str]
    refused: bool
    model: str
    log_id: str
