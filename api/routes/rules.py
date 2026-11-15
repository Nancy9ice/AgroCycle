"""Route: GET /evidence/rules. Read-only view of the engine's rule register in ClickHouse (DS2's engine_* tables)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request

from api.core.rule_register import build_rule_register
from api.db.repository import FieldRepository
from api.deps import get_data_version, get_repository
from api.schemas.rules import RuleRegisterOut
from engine.rules import strategy_rules as rules

router = APIRouter()


@router.get("/evidence/rules", response_model=RuleRegisterOut, tags=["evidence"])
def get_rule_register(
    request: Request, repository: FieldRepository = Depends(get_repository)
) -> RuleRegisterOut:
    """The rules behind every outcome, and how much evidence stands behind each.

    Applicability rules (with whether each is team-proposed or drawn from the experiment, and whether an expert
    has reviewed it), the crop-claim register (sourced or research needed), what each outcome may claim, and
    the three strategies. This is the engine's rule table, not a stress test or a transition plan.
    """
    try:
        raw = repository.get_rule_register()
    except Exception as err:
        raise HTTPException(status_code=503, detail=f"The rule register could not be read: {err}") from err
    result = build_rule_register(raw, rules.RULES_VERSION, get_data_version(request))
    if result is None:
        raise HTTPException(status_code=503, detail="No rule register has been loaded yet.")
    return result
