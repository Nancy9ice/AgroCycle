"""Routes: GET /fields/demo, POST /fields, GET /fields, GET /fields/{id},
GET /fields/{id}/profile, GET /fields/{id}/timeseries."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from api.core.cover_calendar import build_cover_calendar
from api.core.crop_summary import describe_sequence
from api.core.demo_fields import field_notes
from api.core.drawn_field import CropHistoryError, classify_crops
from api.core.profile_view import build_profile_view
from api.core.season_summary import build_season_summary
from api.core.validation import validate_geometry
from api.db.facts import DRAWN_PREFIX, FIRST_CROP_YEAR, FieldRecord
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
from api.schemas.cover import CoverCalendarOut
from api.schemas.fields import CropHistoryRequest, DrawnCropHistoryOut
from api.schemas.season import SeasonSummaryOut

DRAWN_SAVED_MESSAGE = (
    "We kept your boundary so you can carry on. No crop, soil or weather data has been prepared for it, so those "
    "show as not assessed. You can tell us what you grew, and the comparison will say what is still missing."
)
CROP_HISTORY_NOTE = (
    "This is what you told us. AgroCycle has not checked it against any map or record, and it is shown as "
    "your input, not as data."
)
# Saving writes to the database for anyone who asks, so cap how many new boundaries can arrive in an hour.
MAX_NEW_DRAWN_FIELDS_PER_HOUR = 300

CUSTOM_FIELD_MESSAGE = (
    "Your boundary is valid, but AgroCycle has only pre-processed data for the demonstration fields. "
    "Crop history, soil, climate and satellite data have not been prepared for this boundary, so it cannot "
    "be compared yet. Choose a demonstration field to see a full comparison."
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
    notes = field_notes()
    classes = {record.field_id: record.field_class for record in repository.list_fields()}  # one query, not 45
    out = []
    for item in repository.list_demo_fields_with_geometry():
        out.append(
            DemoFieldOut(
                **item,
                field_class=classes.get(item["field_id"]),
                **notes.get(item["field_id"], {}),
            )
        )
    return out


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
            can_compare=True,
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
        can_compare=False,
        message=CUSTOM_FIELD_MESSAGE,
        coverage=[
            SourceCoverageOut(source_id="cdl", status="not_assessed", note="Not pre-processed for this boundary"),
            SourceCoverageOut(source_id="power", status="not_assessed", note="Not pre-processed for this boundary"),
            SourceCoverageOut(source_id="ssurgo", status="not_assessed", note="Not pre-processed for this boundary"),
            SourceCoverageOut(source_id="hls", status="not_assessed", note="Not pre-processed for this boundary"),
        ],
        data_version=dv,
    )


def _not_assessed_coverage() -> list[SourceCoverageOut]:
    return [
        SourceCoverageOut(source_id=source, status="not_assessed", note="Not pre-processed for this boundary")
        for source in ("cdl", "power", "ssurgo", "hls")
    ]


@router.post("/fields/drawn", response_model=FieldValidationOut, tags=["fields"])
def save_drawn_field(
    body: FieldInputRequest,
    request: Request,
    repository: FieldRepository = Depends(get_repository),
) -> FieldValidationOut:
    """Validate a boundary the farmer drew and keep it, so they can carry on to a profile for it.

    Nothing is pre-processed for a drawn boundary: its profile shows crop, soil and weather as not assessed, and
    the comparison says what is missing. The farmer can add their own crop history (`POST /fields/{id}/crop-history`).
    """
    dv = get_data_version(request)
    if body.geometry is None:
        raise HTTPException(status_code=422, detail="Provide a geometry.")
    if body.geometry.get("type") != "Polygon":
        errors, area_ha, county = (
            [{"code": "not_a_polygon", "message": "Draw one field as a single polygon."}], None, None,
        )
    else:
        errors, area_ha, county = validate_geometry(body.geometry)
    if errors or county is None or area_ha is None:
        return FieldValidationOut(
            field_id="", valid=False, errors=[ValidationError(**e) for e in errors], name=body.name,
            county=county, area_ha=area_ha, boundary_source="drawn", role=None, is_demo=False,
            in_pilot_area=county is not None, is_preprocessed=False, coverage=[], data_version=dv,
        )
    try:
        if repository.count_recent_drawn_fields(1) >= MAX_NEW_DRAWN_FIELDS_PER_HOUR:
            raise HTTPException(status_code=429, detail="Too many boundaries were saved in the last hour. Try again later.")
        field_id = f"{DRAWN_PREFIX}{uuid.uuid4().hex[:8]}"
        repository.save_drawn_field(field_id, body.name or field_id, county, round(area_ha, 2), body.geometry)
    except HTTPException:
        raise
    except Exception as err:
        raise HTTPException(status_code=503, detail=f"Your boundary could not be saved: {err}") from err
    return FieldValidationOut(
        field_id=field_id, valid=True, errors=[], name=body.name or field_id, county=county, area_ha=area_ha,
        boundary_source="drawn", role="drawn", is_demo=False, in_pilot_area=True, is_preprocessed=False,
        can_continue=True, can_compare=False, message=DRAWN_SAVED_MESSAGE,
        coverage=_not_assessed_coverage(), data_version=dv,
    )


@router.post("/fields/{field_id}/crop-history", response_model=DrawnCropHistoryOut, tags=["fields"])
def set_crop_history(
    field_id: str, body: CropHistoryRequest, repository: FieldRepository = Depends(get_repository)
) -> DrawnCropHistoryOut:
    """The farmer's own crop for each of the last 11 seasons (2015 to 2025), for a boundary they drew.

    The field's class comes from DS1's classification rules, the same ones the pre-processed fields go through.
    It is stored and shown as the farmer's input, never as CDL data.
    """
    if not field_id.startswith(DRAWN_PREFIX):
        raise HTTPException(status_code=422, detail="Crop history can only be given for a boundary you drew.")
    try:
        sequence, field_class = classify_crops(list(body.crops))
    except CropHistoryError as err:
        raise HTTPException(status_code=422, detail=str(err)) from err
    try:
        found = repository.set_drawn_crop_history(field_id, sequence, field_class)
    except Exception as err:
        raise HTTPException(status_code=503, detail=f"Your answers could not be saved: {err}") from err
    if not found:
        raise HTTPException(status_code=404, detail=f"No field with id {field_id!r}.")
    return DrawnCropHistoryOut(
        field_id=field_id, field_class=field_class, crop_sequence=sequence,
        summary=describe_sequence(sequence, FIRST_CROP_YEAR), evidence_note=CROP_HISTORY_NOTE,
    )


@router.get("/fields/{field_id}/detail", response_model=DemoFieldOut, tags=["fields"])
def field_detail(
    field_id: str, repository: FieldRepository = Depends(get_repository)
) -> DemoFieldOut:
    """One field with its boundary, for the map and the pages. Works for demonstration and drawn fields."""
    record = _require_field(repository, field_id)
    if record.role == "drawn":
        row = repository.get_drawn_field(field_id)
        if row is None:
            raise HTTPException(status_code=404, detail=f"No field with id {field_id!r}.")
        from shapely.geometry import shape

        centroid = shape(row["geometry"]).centroid
        return DemoFieldOut(
            field_id=field_id, county=row["county"], role="drawn", boundary_source="drawn", is_demo=False,
            area_ha=round(row["area_ha"], 1), geometry=row["geometry"], field_class=record.field_class,
            domain_note="", provenance="Drawn by you. No data was pre-processed for this boundary.",
            cover_detail=None, centroid=[round(centroid.x, 6), round(centroid.y, 6)],
        )
    match = next((f for f in list_demo_fields(repository) if f.field_id == field_id), None)
    if match is None:
        raise HTTPException(status_code=404, detail=f"No field with id {field_id!r}.")
    return match


@router.get("/fields", response_model=list[FieldOut], tags=["fields"])
def list_fields(repository: FieldRepository = Depends(get_repository)) -> list[FieldOut]:
    return [_field_out(record) for record in repository.list_fields()]


@router.get("/fields/{field_id}", response_model=FieldOut, tags=["fields"])
def get_field(field_id: str, repository: FieldRepository = Depends(get_repository)) -> FieldOut:
    return _field_out(_require_field(repository, field_id))


@router.get("/fields/{field_id}/profile", response_model=FieldProfileOut, tags=["fields"])
def get_profile(
    field_id: str, request: Request, repository: FieldRepository = Depends(get_repository)
) -> FieldProfileOut:
    """Crop history, weather and soil for one field, each with its provenance.

    Only real values. A section with nothing behind it says `not_loaded`; sample values are never served.
    """
    record = _require_field(repository, field_id)
    return build_profile_view(record, repository.get_indicators(field_id), get_data_version(request))


@router.get("/fields/{field_id}/season-summary", response_model=SeasonSummaryOut, tags=["fields"])
def get_season_summary(
    field_id: str, request: Request, repository: FieldRepository = Depends(get_repository)
) -> SeasonSummaryOut:
    """How hot, dry, wet and warm each past season was in this field's weather cell.

    A season stress summary: heat days, the longest dry run, dry spells, rain and growing degree days for every
    season on record, with the lineage limits attached. It counts past weather over the whole season. It does not
    say when in the season anything happened, so it is not a crop-phase stress test.
    """
    _require_field(repository, field_id)
    return build_season_summary(field_id, repository.get_indicator_rows(field_id), get_data_version(request))


@router.get("/fields/{field_id}/cover-calendar", response_model=CoverCalendarOut, tags=["fields"])
def get_cover_calendar(
    field_id: str, request: Request, repository: FieldRepository = Depends(get_repository)
) -> CoverCalendarOut:
    """What satellite images say about cover on this field, month by month, for the years we have images.

    Each month is bare, likely bare (inside a bare window but without a usable image that month), green, or
    unknown. It says nothing about which crop grew (NDVI is greenness) and nothing about what a different rotation
    would look like: no sourced timing exists for that. Returns 404 when the field has no images.
    """
    _require_field(repository, field_id)
    rows = repository.get_cover_rows(field_id)
    result = build_cover_calendar(field_id, rows["ndvi"], rows["bare_windows"], get_data_version(request))
    if result is None:
        raise HTTPException(status_code=404, detail="No satellite images have been loaded for this field.")
    return result


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
