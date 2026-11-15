"""Route: GET /strategies/{id}/transition. DS2's transition sequence for switching to B or C, read-only."""
from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from api.core.transition import SWITCHABLE, build_transition
from api.db.repository import FieldRepository
from api.deps import get_data_version, get_repository
from api.schemas.transition import TransitionOut

router = APIRouter()


@router.get("/strategies/{strategy_id}/transition", response_model=TransitionOut, tags=["compare"])
def get_transition(
    strategy_id: str,
    request: Request,
    analysis_id: str | None = Query(default=None, max_length=64, description="A saved comparison, for the readiness check."),
    repository: FieldRepository = Depends(get_repository),
) -> TransitionOut:
    """The year-by-year sequence for switching from the two-year rotation to strategy B or C.

    Only what the Marsden experiment establishes: the sequence, the manure (applied in October), and needs read from
    the rotation definition (marked as the team's own). Every other timing says it is not established. With an
    `analysis_id` it also lists which of the farmer's own answers bear on which step.
    """
    strategy_id = strategy_id.upper()
    if strategy_id not in SWITCHABLE:
        raise HTTPException(status_code=404, detail="There is a switch plan for strategies B and C only: A is the system you already run.")
    constraints = None
    if analysis_id is not None:
        stored = repository.get_analysis(analysis_id)
        if stored is None:
            raise HTTPException(status_code=404, detail=f"No analysis with id {analysis_id!r}.")
        constraints = json.loads(stored["response_json"])["decision"]["constraints_recorded"]
    try:
        rows = repository.get_transition_steps(strategy_id)
    except Exception as err:
        raise HTTPException(status_code=503, detail=f"The transition sequence could not be read: {err}") from err
    result = build_transition(strategy_id, rows, get_data_version(request), constraints)
    if result is None:
        raise HTTPException(status_code=503, detail="No transition sequence has been loaded yet.")
    return result
