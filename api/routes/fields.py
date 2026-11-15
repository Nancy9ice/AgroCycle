"""Routes: GET /fields/demo, POST /fields, GET /fields, GET /fields/{id},
GET /fields/{id}/profile, GET /fields/{id}/timeseries."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from api.core.profile_view import build_profile_view
from api.core.validation import validate_geometry
from api.db.facts import FieldRecord
from api.db.repository import FieldRepository
from api.deps import DEMO_COVERAGE, get_data_version, get_repository
from api.schemas import (
    DemoFieldOut,
    FieldInputRequest,
    FieldOut,
    FieldProfileOut,
    FieldValidationOut,
    SourceCoverageOut,
    TimeSeriesOut,
    TimeSeriesPointOut,
    ValidationError,
)

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
        points_raw = repository.get_ndvi_timeseries(field_id, from_date, to_date)
        points = [TimeSeriesPointOut(**p) for p in points_raw]
        return TimeSeriesOut(field_id=field_id, kind=kind, from_date=from_date, to_date=to_date, max_points=max_points, points=points, data_version=dv)
    points_raw = repository.get_climate_timeseries(field_id, from_date, to_date, max_points)
    points = [TimeSeriesPointOut(**p) for p in points_raw]
    return TimeSeriesOut(field_id=field_id, kind=kind, from_date=from_date, to_date=to_date, max_points=max_points, points=points, data_version=dv)
