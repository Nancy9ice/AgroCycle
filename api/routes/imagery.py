"""Routes: GET /fields/{id}/imagery (what there is) and GET /fields/{id}/imagery/image.png (the picture)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, Response

from api.core.imagery import ATTRIBUTION, ChipRecord, ImageryError, render_chip
from api.db.imagery import ImagerySource
from api.deps import get_repository
from api.schemas.imagery import ImageryOut, ImageryTileOut

router = APIRouter()

NOTE = (
    "One aerial photo from one day, not a crop map. It shows what the field looked like when it was flown, "
    "and may not match the crops you grow today."
)


def get_imagery(request: Request) -> ImagerySource:
    return request.app.state.imagery


def _records(field_id: str, repository, imagery: ImagerySource) -> list[ChipRecord]:
    if repository.get_field(field_id) is None:
        raise HTTPException(status_code=404, detail=f"No field with id {field_id!r}.")
    try:
        return imagery.records(field_id)
    except Exception as err:
        raise HTTPException(status_code=503, detail=f"The photo index could not be read: {err}") from err


def _render(records: list[ChipRecord], imagery: ImagerySource):
    # A field cut from two tiles has two rows that point at the same chip file: read it once.
    try:
        return render_chip(imagery.chip(records[0]))
    except ImageryError as err:
        raise HTTPException(status_code=503, detail=str(err)) from err


@router.get("/fields/{field_id}/imagery", response_model=ImageryOut, tags=["fields"])
def get_field_imagery(
    field_id: str, repository=Depends(get_repository), imagery: ImagerySource = Depends(get_imagery)
) -> ImageryOut:
    records = _records(field_id, repository, imagery)
    if not records:
        return ImageryOut(field_id=field_id, available=False)
    rendered = _render(records, imagery)
    first = records[0]
    return ImageryOut(
        field_id=field_id, available=True, year=first.year,
        tiles=[ImageryTileOut(tile_id=r.tile_id, flight_date=r.flight_date.isoformat()) for r in records],
        resolution_m=first.resolution_m, bounds=list(rendered.bounds),
        evidence_type=first.evidence_type, attribution=ATTRIBUTION, note=NOTE,
    )


@router.get("/fields/{field_id}/imagery/image.png", tags=["fields"], response_class=Response)
def get_field_imagery_image(
    field_id: str, repository=Depends(get_repository), imagery: ImagerySource = Depends(get_imagery)
) -> Response:
    records = _records(field_id, repository, imagery)
    if not records:
        raise HTTPException(status_code=404, detail="No aerial photo for this field.")
    return Response(content=_render(records, imagery).png, media_type="image/png")
