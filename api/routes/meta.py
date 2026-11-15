"""Routes: /health, /meta/constraint-options."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from api.db.meta import CONSTRAINT_OPTIONS
from api.db.repository import FieldRepository
from api.deps import get_data_version, get_repository
from api.schemas import ConstraintQuestionOut, HealthOut, MetaConstraintOptionsOut
from engine.rules import strategy_rules as rules

router = APIRouter()


@router.get("/health", response_model=HealthOut, tags=["meta"])
def health(
    request: Request,
    repository: FieldRepository = Depends(get_repository),
) -> HealthOut:
    ch_client = getattr(request.app.state, "ch_client", None)
    clickhouse_ok = False
    if ch_client is not None:
        try:
            ch_client.query("SELECT 1")
            clickhouse_ok = True
        except Exception:
            clickhouse_ok = False
    return HealthOut(
        status="ok" if (ch_client is None or clickhouse_ok) else "degraded",
        data_source=repository.name,
        rules_version=rules.RULES_VERSION,
        clickhouse=clickhouse_ok,
        data_version=get_data_version(request),
    )


@router.get("/meta/constraint-options", response_model=MetaConstraintOptionsOut, tags=["meta"])
def constraint_options() -> MetaConstraintOptionsOut:
    return MetaConstraintOptionsOut(
        questions=[ConstraintQuestionOut(**q) for q in CONSTRAINT_OPTIONS]
    )
