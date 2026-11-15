"""Routes: POST /fields/{id}/compare, GET /analyses/{id}."""
from __future__ import annotations

import json
import logging
import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Request

from api.core.profile import build_profile
from api.core.serialise import to_plain
from api.db.facts import FieldRecord
from api.db.repository import FieldRepository
from api.deps import get_data_version, get_repository, get_settings
from api.schemas import CompareRequest, CompareResponse, FieldOut
from api.settings import Settings
from engine import decision as engine
from engine.rules import strategy_rules as rules

_log = logging.getLogger("agrocycle")
router = APIRouter()


def _field_out(record: FieldRecord) -> FieldOut:
    return FieldOut(
        field_id=record.field_id,
        county=record.county,
        boundary_source=record.boundary_source,  # type: ignore[arg-type]
        role=record.role,  # type: ignore[arg-type]
        field_class=record.field_class,
    )


def _require_field(repository: FieldRepository, field_id: str) -> FieldRecord:
    record = repository.get_field(field_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"No field with id {field_id!r}.")
    return record


@router.post("/fields/{field_id}/compare", response_model=CompareResponse, tags=["compare"])
def compare(
    field_id: str,
    body: CompareRequest,
    request: Request,
    repository: FieldRepository = Depends(get_repository),
    settings: Settings = Depends(get_settings),
) -> CompareResponse:
    """Compare the three strategies for one field.

    Returns one of three outcomes (worth exploring, qualified comparison, abstention) with the reasons.
    There is no score, no ranking and no winner. The server builds the field profile; the request only
    carries what the farmer said.
    """
    record = _require_field(repository, field_id)
    if body.sample_indicators and not settings.allow_sample_preview:
        raise HTTPException(status_code=403, detail="Sample-indicator previews are disabled.")

    profile = build_profile(
        record, repository.get_indicators(field_id), sample_indicators=body.sample_indicators
    )
    constraints = engine.FarmerConstraints.from_mapping(
        {
            "manure_access": body.manure_access,
            "forage_use_or_buyer": body.forage_use_or_buyer,
            "oat_use_or_buyer": body.oat_use_or_buyer,
            "small_grain_equipment_or_contractor": body.small_grain_equipment_or_contractor,
            "priorities": body.priorities,
        }
    )
    decision = engine.assess(profile, constraints)
    dv = get_data_version(request)
    analysis_id = f"a_{uuid.uuid4().hex[:6]}"
    created_at = datetime.now(UTC).isoformat()

    response = CompareResponse.model_validate(
        {
            "field": _field_out(record),
            "decision": to_plain(decision),
            "preview": body.sample_indicators,
            "context_recorded": body.context,
            "analysis_id": analysis_id,
            "created_at": created_at,
            "engine_version": rules.RULES_VERSION,
            "data_version": dv,
        }
    )
    # A storage problem must not break the comparison, but the caller is told when the result was not kept.
    try:
        repository.store_analysis(
            analysis_id=analysis_id,
            field_id=field_id,
            engine_version=rules.RULES_VERSION,
            data_version=dv,
            response_json=response.model_dump_json(),
        )
    except Exception:
        _log.exception("Could not store analysis %s for field %s", analysis_id, field_id)
        response.persistence = "failed"
        response.persistence_warning = (
            "This comparison could not be saved, so its share link will not open later. "
            "The result above is still correct; run it again to get a link."
        )
    else:
        if not getattr(repository, "durable_analyses", False):
            response.persistence = "temporary"
            response.persistence_warning = (
                "This comparison is held in memory only and will be lost when the server restarts."
            )
    return response


@router.get("/analyses/{analysis_id}", response_model=CompareResponse, tags=["compare"])
def get_analysis(
    analysis_id: str,
    repository: FieldRepository = Depends(get_repository),
) -> CompareResponse:
    stored = repository.get_analysis(analysis_id)
    if stored is None:
        raise HTTPException(status_code=404, detail=f"No analysis with id {analysis_id!r}.")
    return CompareResponse.model_validate(json.loads(stored["response_json"]))
