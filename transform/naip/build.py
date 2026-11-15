"""Build the naip_tiles index from the manifests of the chips in S3 (Phase 12, DE).

One row per field and source tile. Everything comes from the manifest beside each chip; nothing is
re-measured. The flight date of each tile is the date in its NAIP name (the last part, YYYYMMDD), and
must be one of the flight dates the manifest lists.
"""

import json
import re
from datetime import date

import pandas as pd

from common.schemas import NAIP_TILES

SOURCE_ID = "naip_2025"
PREFIX = "raw/naip/naip-2025/"
MANIFEST_SUFFIX = ".manifest.json"
RESOLUTION_M = {2025: 0.6}  # the catalogue's ground sample distance for the 2025 Iowa flights
_TILE_DATE = re.compile(r"_(\d{8})$")
COLUMNS = list(NAIP_TILES.columns)


class NaipBuildError(RuntimeError):
    pass


def tile_flight_date(tile_id: str) -> date:
    match = _TILE_DATE.search(tile_id)
    if not match:
        raise NaipBuildError(f"tile {tile_id!r} has no flight date in its name")
    text = match.group(1)
    return date(int(text[:4]), int(text[4:6]), int(text[6:]))


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
    """Read-only. The newest retrieval date under raw/naip/naip-2025/."""
    keys = [o["Key"] for page in client.get_paginator("list_objects_v2").paginate(Bucket=bucket, Prefix=PREFIX)
            for o in page.get("Contents", []) if o["Key"].endswith(MANIFEST_SUFFIX)]
    if not keys:
        raise NaipBuildError(f"no manifests under {PREFIX}")
    newest = max(k.split("/")[3] for k in keys)
    return {k: json.loads(client.get_object(Bucket=bucket, Key=k)["Body"].read())
            for k in keys if k.split("/")[3] == newest}
