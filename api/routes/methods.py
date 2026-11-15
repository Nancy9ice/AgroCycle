"""Routes: GET /evidence/marsden, GET /lineage/{id}, GET /sources, GET /indicators."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request

from api.db.repository import FieldRepository
from api.deps import get_data_version, get_repository
from api.schemas import (
    IndicatorGlossaryOut,
    LineageOut,
    MarsdenEvidenceOut,
    MarsdenRowOut,
    SourceOut,
)

router = APIRouter()


@router.get("/evidence/marsden", response_model=MarsdenEvidenceOut, tags=["evidence"])
def evidence_marsden(
    request: Request,
    repository: FieldRepository = Depends(get_repository),
) -> MarsdenEvidenceOut:
    rows = repository.get_marsden_means()
    dv = get_data_version(request)
    return MarsdenEvidenceOut(
        title="Marsden Farm Experiment — Reproduced Management Data",
        description=(
            "Davis et al. (2012) compared three crop-rotation systems at Marsden Farm, Iowa, "
            "from 2003 to 2011. These are the rotation-area-weighted nine-year mean management values, "
            "reproduced from the paper's supplementary tables."
        ),
        rows=[MarsdenRowOut(**r) for r in rows],
        caveats=[
            "One research farm in Iowa, 2003–2011. Not a field-scale prediction.",
            "Applied N = manufactured N + manure N. Biological N fixation is excluded.",
            "Yields are attributed to Davis et al. (2012), not independently recomputed.",
            "Soil carbon, erosion and nitrate leaching are not claimed: data exists but causal attribution is not possible.",
            "One discrepancy remains unreconciled: 2-yr manufactured N is 74.5 kg/ha/yr from Table S3 but 80 kg/ha/yr in the paper's text. Traced to 2011; cause unknown.",
        ],
        reference="Davis, A.S. et al. (2012). Increasing Cropping System Diversity Balances Productivity, Profitability and Environmental Health. PLOS ONE 7(10): e47149.",
        data_version=dv,
    )


@router.get("/lineage/{indicator_id}", response_model=LineageOut, tags=["methods"])
def get_lineage(
    indicator_id: str,
    repository: FieldRepository = Depends(get_repository),
) -> LineageOut:
    row = repository.get_lineage_row(indicator_id)
    if row is None:
        raise HTTPException(status_code=404, detail=f"No lineage record for indicator {indicator_id!r}.")
    return LineageOut(**row)


@router.get("/sources", response_model=list[SourceOut], tags=["methods"])
def list_sources(repository: FieldRepository = Depends(get_repository)) -> list[SourceOut]:
    return [SourceOut(**r) for r in repository.get_all_sources()]


@router.get("/indicators", response_model=list[IndicatorGlossaryOut], tags=["methods"])
def list_indicators(repository: FieldRepository = Depends(get_repository)) -> list[IndicatorGlossaryOut]:
    return [IndicatorGlossaryOut(**r) for r in repository.get_all_lineage()]
