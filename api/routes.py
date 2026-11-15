"""HTTP endpoints. They validate, look up, call the engine and serialise; they decide nothing."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request

from engine import decision as engine
from engine.rules import strategy_rules as rules

from .facts import FieldRecord
from .profile import build_profile
from .profile_view import build_profile_view
from .repository import FieldRepository
from .schemas import CompareRequest, CompareResponse, FieldOut, FieldProfileOut, HealthOut
from .serialise import to_plain
from .settings import Settings

router = APIRouter()


def get_repository(request: Request) -> FieldRepository:
    return request.app.state.repository


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


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


@router.get("/health", response_model=HealthOut, tags=["meta"])
def health(
    repository: FieldRepository = Depends(get_repository),
) -> HealthOut:
    return HealthOut(status="ok", data_source=repository.name, rules_version=rules.RULES_VERSION)


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


@router.post("/fields/{field_id}/compare", response_model=CompareResponse, tags=["compare"])
def compare(
    field_id: str,
    body: CompareRequest,
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
    return CompareResponse.model_validate(
        {
            "field": _field_out(record),
            "decision": to_plain(decision),
            "preview": body.sample_indicators,
        }
    )
