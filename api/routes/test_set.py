"""Route: GET /validation/test-set (F5). Read-only view of DS's Phase 14 audit in ClickHouse."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request

from api.core.test_set import build_test_set
from api.db.repository import FieldRepository
from api.deps import get_data_version, get_repository
from api.schemas.test_set import TestSetOut

router = APIRouter()


@router.get("/validation/test-set", response_model=TestSetOut, tags=["validation"])
def get_test_set(
    request: Request, repository: FieldRepository = Depends(get_repository)
) -> TestSetOut:
    try:
        rows = repository.get_test_set_rows()
    except Exception as err:
        raise HTTPException(status_code=503, detail=f"The test-set audit could not be read: {err}") from err
    result = build_test_set(rows, get_data_version(request))
    if result is None:
        raise HTTPException(status_code=503, detail="No engine run of the test set has been loaded yet.")
    return result
