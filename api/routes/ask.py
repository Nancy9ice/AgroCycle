"""Routes: POST /fields/{id}/ask, POST /analyses/{id}/ask."""
from __future__ import annotations

import json
import uuid

from fastapi import APIRouter, Depends, HTTPException

from api.core.ask import build_analysis_context, build_profile_context, call_claude
from api.db.repository import FieldRepository
from api.deps import get_repository
from api.schemas import AskRequest, AskResponse

router = APIRouter()


def _require_field(repository, field_id: str):
    record = repository.get_field(field_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"No field with id {field_id!r}.")
    return record


@router.post("/analyses/{analysis_id}/ask", response_model=AskResponse, tags=["ask"])
def ask_analysis(
    analysis_id: str,
    body: AskRequest,
    repository: FieldRepository = Depends(get_repository),
) -> AskResponse:
    """Answer one question about a stored comparison result.

    Context is built from the stored analysis JSON + all indicator lineage rows.
    The model only sees that context — no outside knowledge. Every Q&A is logged.
    Label the panel "AI explanation of AgroCycle's computed results" in the UI.
    """
    stored = repository.get_analysis(analysis_id)
    if stored is None:
        raise HTTPException(status_code=404, detail=f"No analysis with id {analysis_id!r}.")

    try:
        analysis = json.loads(stored["response_json"])
    except Exception:
        raise HTTPException(status_code=503, detail="Stored analysis could not be parsed.")

    lineage_rows = repository.get_all_lineage()
    context, indicator_ids = build_analysis_context(analysis, lineage_rows)

    result = call_claude(context, indicator_ids, body.question, body.audience)

    log_id = f"ask_{uuid.uuid4().hex[:8]}"
    field_id = analysis.get("field", {}).get("field_id", "")
    try:
        repository.log_ask(
            log_id=log_id,
            context_type="analysis",
            context_id=analysis_id,
            field_id=field_id,
            question=body.question,
            answer=result["answer"],
            citations=result["citations"],
            refused=result["refused"],
            audience=body.audience,
            model=result["model"],
        )
    except Exception:
        pass  # logging failure must not block the response

    return AskResponse(**result, log_id=log_id)


@router.post("/fields/{field_id}/ask", response_model=AskResponse, tags=["ask"])
def ask_field(
    field_id: str,
    body: AskRequest,
    repository: FieldRepository = Depends(get_repository),
) -> AskResponse:
    """Answer one question about a field's environmental profile.

    Context is built from the field record + indicator facts + lineage rows.
    Useful on the Profile screen before the farmer has run a comparison.
    """
    record = _require_field(repository, field_id)
    facts = repository.get_indicators(field_id)
    lineage_rows = repository.get_all_lineage()
    context, indicator_ids = build_profile_context(record, facts, lineage_rows)

    result = call_claude(context, indicator_ids, body.question, body.audience)

    log_id = f"ask_{uuid.uuid4().hex[:8]}"
    try:
        repository.log_ask(
            log_id=log_id,
            context_type="field",
            context_id=field_id,
            field_id=field_id,
            question=body.question,
            answer=result["answer"],
            citations=result["citations"],
            refused=result["refused"],
            audience=body.audience,
            model=result["model"],
        )
    except Exception:
        pass

    return AskResponse(**result, log_id=log_id)
