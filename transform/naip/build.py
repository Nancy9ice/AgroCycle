"""Build the naip_tiles index from the manifests of the chips in S3 (Phase 12, DE).

One row per field and source tile. size_bytes and sha256 describe the whole chip, so a field cut from
two tiles repeats them on both rows: sum over distinct s3_key, never over rows. Everything comes from the manifest beside each chip; nothing is
re-measured. The flight date of each tile is the date in its NAIP name (the last part, YYYYMMDD), and
must be one of the flight dates the manifest lists.
"""

import json
from datetime import date

import pandas as pd

from common.schemas import NAIP_TILES
from ingest.naip import flight_date_from_id

SOURCE_ID = "naip_2025"
PREFIX = "raw/naip/naip-2025/"
MANIFEST_SUFFIX = ".manifest.json"
RESOLUTION_M = {2025: 0.6}  # the catalogue's ground sample distance for the 2025 Iowa flights
COLUMNS = list(NAIP_TILES.columns)


class NaipBuildError(RuntimeError):
    pass


def tile_flight_date(tile_id: str) -> date:
    try:
        return flight_date_from_id(tile_id)
    except ValueError as err:
        raise NaipBuildError(str(err)) from None


def rows_from_manifest(key: str, manifest: dict) -> list[dict]:
    subset = manifest["subset"]
    if subset.get("kind") != "field_chip":
        raise NaipBuildError(f"{key}: not a field chip manifest")
    year = int(subset["year"])
    if year not in RESOLUTION_M:
        raise NaipBuildError(f"{key}: no known resolution for NAIP {year}")
    lon0, lat0, lon1, lat1 = subset["bbox"]
    listed = set(subset["flight_dates"])
    rows = []
    for tile_id in subset["tiles"]:
        flown = tile_flight_date(tile_id)
        if flown.isoformat() not in listed:
            raise NaipBuildError(f"{key}: tile {tile_id} flown {flown} is not among the manifest's flight dates")
        rows.append({
            "field_id": subset["field_id"], "year": year, "tile_id": tile_id,
            "flight_date": pd.Timestamp(flown), "resolution_m": RESOLUTION_M[year],
            "bbox_min_lon": lon0, "bbox_min_lat": lat0, "bbox_max_lon": lon1, "bbox_max_lat": lat1,
            "buffer_m": float(subset["buffer_m"]), "bands": ",".join(subset["bands"]),
            "s3_key": key[: -len(MANIFEST_SUFFIX)], "size_bytes": int(manifest["size_bytes"]),
            "sha256": manifest["sha256"], "retrieval_date": pd.Timestamp(manifest["retrieval_date"]),
            "evidence_type": manifest["evidence_type"], "source_id": SOURCE_ID,
        })
    return rows


def build(manifests: dict[str, dict]) -> pd.DataFrame:
    """The validated naip_tiles frame from {manifest key: manifest dict}."""
    if not manifests:
        raise NaipBuildError("no NAIP manifests found")
    rows = [row for key, m in sorted(manifests.items()) for row in rows_from_manifest(key, m)]
    frame = pd.DataFrame(rows, columns=COLUMNS).astype({"resolution_m": "float64", "buffer_m": "float64"})
    return NAIP_TILES.validate(frame)


def read_s3_manifests(client, bucket: str) -> dict[str, dict]:
    """Read-only. Every retrieval date under raw/naip/naip-2025/, the newest manifest for each chip.

    A pull spread over several days (a resumed run) is read whole; taking only the newest date would
    drop the fields pulled earlier.
    """
    keys = [o["Key"] for page in client.get_paginator("list_objects_v2").paginate(Bucket=bucket, Prefix=PREFIX)
            for o in page.get("Contents", []) if o["Key"].endswith(MANIFEST_SUFFIX)]
    if not keys:
        raise NaipBuildError(f"no manifests under {PREFIX}")
    newest: dict[str, str] = {}
    for key in sorted(keys, key=lambda k: k.split("/")[3]):  # oldest first, so the newest date wins
        newest[key.rsplit("/", 1)[1]] = key
    return {k: json.loads(client.get_object(Bucket=bucket, Key=k)["Body"].read()) for k in newest.values()}
