"""Schemas for GET /validation/test-set (F5, "How we tested this")."""
from __future__ import annotations

from pydantic import BaseModel


class ScenarioOutcomeOut(BaseModel):
    scenario: str
    outcome: str


class TestSetFieldOut(BaseModel):
    __test__ = False  # not a pytest class

    field_id: str
    role: str | None
    county: str | None
    sequence_summary: str
    expected_outcome: str
    engine_outcome: str
    match: bool
    scenarios: list[ScenarioOutcomeOut]


class CdlAgreementOut(BaseModel):
    reference: str
    metrics: dict
    note: str


class TestSetOut(BaseModel):
    __test__ = False

    data_version: str
    engine_version: str
    run_id: str
    headline_scenario: str
    fields: list[TestSetFieldOut]
    outcome_counts: dict[str, int]
    match_count: int
    cdl_agreement: CdlAgreementOut
    caveats: list[str]
