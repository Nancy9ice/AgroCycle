"""Backward-compatibility shim — the real routes live in api/routes/ package.
Python loads the package (api/routes/__init__.py) in preference to this file."""
from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from engine import decision as engine
from engine.rules import strategy_rules as rules

from .ask import build_analysis_context, build_profile_context, call_claude
from .facts import FieldRecord
from .meta import CONSTRAINT_OPTIONS
from .profile import build_profile
from .profile_view import build_profile_view
from .repository import FieldRepository
from .schemas import (
    AskRequest,
    AskResponse,
    CompareRequest,
    CompareResponse,
    ConstraintQuestionOut,
    DemoFieldOut,
    FieldInputRequest,
    FieldOut,
    FieldProfileOut,
    FieldValidationOut,
    HealthOut,
    IndicatorGlossaryOut,
    LineageOut,
    MarsdenEvidenceOut,
    MarsdenRowOut,
    MetaConstraintOptionsOut,
    SourceCoverageOut,
    SourceOut,
    TimeSeriesOut,
    TimeSeriesPointOut,
    ValidationError,
)
from .serialise import to_plain
from .settings import Settings
from .validation import validate_geometry

router = APIRouter()

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


# ---------------------------------------------------------------------------
# Meta
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Fields
# ---------------------------------------------------------------------------

@router.get("/fields/demo", response_model=list[DemoFieldOut], tags=["fields"])
def list_demo_fields(repository: FieldRepository = Depends(get_repository)) -> list[DemoFieldOut]:
    items = repository.list_demo_fields_with_geometry()
    return [DemoFieldOut(**item) for item in items]


@router.post("/fields", response_model=FieldValidationOut, tags=["fields"])
def validate_field(
    body: FieldInputRequest,
    request: Request,
    repository: FieldRepository = Depends(get_repository),
) -> FieldValidationOut:
    dv = get_data_version(request)
    if body.demo_field_id is not None:
        record = repository.get_field(body.demo_field_id)
        if record is None:
            raise HTTPException(status_code=422, detail="Unknown demo field.")
        demo_items = {item["field_id"]: item for item in repository.list_demo_fields_with_geometry()}
        item = demo_items.get(body.demo_field_id, {})
        return FieldValidationOut(
            field_id=body.demo_field_id,
            valid=True,
            errors=[],
            name=body.demo_field_id,
            county=record.county,
            area_ha=item.get("area_ha"),
            boundary_source="demo",
            role=record.role,
            is_demo=True,
            in_pilot_area=True,
            is_preprocessed=True,
            coverage=DEMO_COVERAGE,
            data_version=dv,
        )
    if body.geometry is None:
        raise HTTPException(status_code=422, detail="Provide either demo_field_id or geometry.")
    errors, area_ha, county = validate_geometry(body.geometry)
    if errors:
        return FieldValidationOut(
            field_id="",
            valid=False,
            errors=[ValidationError(**e) for e in errors],
            name=body.name,
            county=county,
            area_ha=area_ha,
            boundary_source=body.boundary_source,
            role=None,
            is_demo=False,
            in_pilot_area=county is not None,
            is_preprocessed=False,
            coverage=[],
            data_version=dv,
        )
    new_id = f"drawn-{uuid.uuid4().hex[:8]}"
    return FieldValidationOut(
        field_id=new_id,
        valid=True,
        errors=[],
        name=body.name or new_id,
        county=county,
        area_ha=area_ha,
        boundary_source=body.boundary_source,
        role=None,
        is_demo=False,
        in_pilot_area=True,
        is_preprocessed=False,
        coverage=[
            SourceCoverageOut(source_id="cdl", status="not_assessed", note="Not pre-processed for this boundary"),
            SourceCoverageOut(source_id="power", status="not_assessed", note="Not pre-processed for this boundary"),
            SourceCoverageOut(source_id="ssurgo", status="not_assessed", note="Not pre-processed for this boundary"),
            SourceCoverageOut(source_id="hls", status="not_assessed", note="Not pre-processed for this boundary"),
        ],
        data_version=dv,
    )


@router.get("/fields", response_model=list[FieldOut], tags=["fields"])
def list_fields(repository: FieldRepository = Depends(get_repository)) -> list[FieldOut]:
    return [_field_out(record) for record in repository.list_fields()]


@router.get("/fields/{field_id}", response_model=FieldOut, tags=["fields"])
def get_field(field_id: str, repository: FieldRepository = Depends(get_repository)) -> FieldOut:
    return _field_out(_require_field(repository, field_id))


@router.get("/fields/{field_id}/profile", response_model=FieldProfileOut, tags=["fields"])
def get_profile(
    field_id: str, repository: FieldRepository = Depends(get_repository)
) -> FieldProfileOut:
    """Crop history, weather and soil for one field, each with its provenance.

    Only real values. A section with nothing behind it says `not_loaded`; sample values are never served.
    """
    record = _require_field(repository, field_id)
    return build_profile_view(record, repository.get_indicators(field_id))


@router.get("/fields/{field_id}/timeseries", response_model=TimeSeriesOut, tags=["fields"])
def get_timeseries(
    field_id: str,
    request: Request,
    kind: str = Query(default="climate", pattern="^(climate|ndvi)$"),
    from_date: str = Query(default="2015-01-01", alias="from"),
    to_date: str = Query(default="2024-12-31", alias="to"),
    max_points: int = Query(default=365, ge=10, le=3650),
    repository: FieldRepository = Depends(get_repository),
) -> TimeSeriesOut:
    _require_field(repository, field_id)
    dv = get_data_version(request)
    if kind == "ndvi":
        return TimeSeriesOut(field_id=field_id, kind=kind, from_date=from_date, to_date=to_date, max_points=max_points, points=[], data_version=dv)
    points_raw = repository.get_climate_timeseries(field_id, from_date, to_date, max_points)
    points = [TimeSeriesPointOut(**p) for p in points_raw]
    return TimeSeriesOut(field_id=field_id, kind=kind, from_date=from_date, to_date=to_date, max_points=max_points, points=points, data_version=dv)


# ---------------------------------------------------------------------------
# Compare and analyses
# ---------------------------------------------------------------------------

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
            "analysis_id": analysis_id,
            "created_at": created_at,
            "engine_version": rules.RULES_VERSION,
            "data_version": dv,
        }
    )
    # Store for later retrieval; best-effort (file mode has in-memory store)
    try:
        repository.store_analysis(
            analysis_id=analysis_id,
            field_id=field_id,
            engine_version=rules.RULES_VERSION,
            data_version=dv,
            response_json=response.model_dump_json(),
        )
    except Exception:
        pass  # don't fail the compare if storage fails
    return response


@router.get("/analyses/{analysis_id}", tags=["compare"])
def get_analysis(
    analysis_id: str,
    repository: FieldRepository = Depends(get_repository),
):
    stored = repository.get_analysis(analysis_id)
    if stored is None:
        raise HTTPException(status_code=404, detail=f"No analysis with id {analysis_id!r}.")
    # Return the stored JSON parsed back
    return json.loads(stored["response_json"])


# ---------------------------------------------------------------------------
# Evidence and methods
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# F1 — Ask AgroCycle (grounded AI assistant)
# ---------------------------------------------------------------------------

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
