"""Where the aerial photos come from: `naip_tiles` in ClickHouse says which chip belongs to which field, and
the chip itself is read from S3. The photo is checked against the checksum in the index before it is used."""
from __future__ import annotations

import hashlib
from typing import Any, Protocol

from api.core.imagery import ChipRecord, ImageryError
from api.db.cache import ttl_cached

CHIP_PREFIX = "raw/naip/"  # a key outside this folder is never read, whatever the table says


class ImagerySource(Protocol):
    def records(self, field_id: str) -> list[ChipRecord]: ...

    def chip(self, record: ChipRecord) -> bytes: ...


class NoImagery:
    """File mode, or no S3: there are no photos, and nothing is invented in their place."""

    def records(self, field_id: str) -> list[ChipRecord]:
        return []

    def chip(self, record: ChipRecord) -> bytes:
        raise ImageryError("aerial photos are not configured for this API")


def _text(value: Any) -> str:
    if isinstance(value, bytes):
        return value.rstrip(b"\x00").decode()
    return str(value)


class ClickHouseS3Imagery:
    _SQL = (
        "SELECT field_id, year, tile_id, flight_date, resolution_m, bbox_min_lon, bbox_min_lat, bbox_max_lon, "
        "bbox_max_lat, buffer_m, bands, s3_key, size_bytes, sha256, evidence_type, source_id "
        "FROM naip_tiles WHERE field_id = {field_id:String} ORDER BY year DESC, tile_id"
    )

    def __init__(self, client: Any, s3: Any, bucket: str) -> None:
        self._client = client
        self._s3 = s3
        self._bucket = bucket

    @ttl_cached()
    def records(self, field_id: str) -> list[ChipRecord]:
        rows = self._client.query(self._SQL, parameters={"field_id": field_id}).result_rows
        return [
            ChipRecord(
                field_id=_text(r[0]), year=int(r[1]), tile_id=_text(r[2]), flight_date=r[3],
                resolution_m=float(r[4]), bbox=(float(r[5]), float(r[6]), float(r[7]), float(r[8])),
                buffer_m=float(r[9]), bands=_text(r[10]), s3_key=_text(r[11]), size_bytes=int(r[12]),
                sha256=_text(r[13]), evidence_type=_text(r[14]), source_id=_text(r[15]),
            )
            for r in rows
        ]

    def chip(self, record: ChipRecord) -> bytes:
        if not record.s3_key.startswith(CHIP_PREFIX):
            raise ImageryError(f"refusing to read {record.s3_key!r}: not under {CHIP_PREFIX}")
        try:
            data = self._s3.get_object(Bucket=self._bucket, Key=record.s3_key)["Body"].read()
        except Exception as err:
            raise ImageryError(f"could not read {record.s3_key} from S3: {err}") from err
        found = hashlib.sha256(data).hexdigest()
        if found != record.sha256:
            raise ImageryError(f"{record.s3_key} does not match its checksum in naip_tiles; not showing it")
        return data
