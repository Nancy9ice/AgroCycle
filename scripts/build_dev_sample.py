"""Build the small dev and test sample for one field and one season (data/sample/).

The sample is derived from the raw pulls already in S3, for primary-001 and the 2023 season:
CDL windows (2015-2025), eight clear HLS scenes, POWER for 2023, and the SSURGO responses.
Every file is listed in data/sample/sample_manifest.json with the S3 object it came from.
It is a sample, not raw data: raw data is only ever read from S3.

Needs the local pull folders written by the extractors. Usage:
    uv run python -m scripts.build_dev_sample
"""

import hashlib
import json
import math
import shutil
from datetime import date
from pathlib import Path

import geopandas as gpd
import rasterio
from rasterio.features import geometry_mask
from rasterio.transform import Affine

from ingest import cdl, hls, power, ssurgo
from ingest.subset import field_bboxes
from transform.field_schema import FIELDS_PATH, ROOT

FIELD = "primary-001"
COUNTY_FIPS = "19169"  # Story
SEASON = 2023
OUT = ROOT / "data" / "sample" / FIELD
CLEAR_BITS = 0b00111110  # HLS Fmask bits 1-5 (NASA User Guide, Table 9)
TARGETS = (date(2023, 4, 15), date(2023, 6, 1), date(2023, 7, 15), date(2023, 9, 1))
RAW_DATE = "2026-11-14"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def cdl_windows(entries: list[dict]) -> None:
    """Cut the field's window (plus 500 m) out of each county clip."""
    fields = gpd.read_file(FIELDS_PATH)
    left, bottom, right, top = gpd.GeoSeries(
        [fields.set_index("field_id").geometry[FIELD]], crs=4326
    ).to_crs(5070).buffer(500).total_bounds
    for year in cdl.YEARS:
        (src_path,) = cdl.default_dir().glob(f"polygonclip_*/CDL_{year}_{COUNTY_FIPS}.tif")
        with rasterio.open(src_path) as src:
            col0, row0 = math.floor((left - src.transform.c) / 30), math.floor((src.transform.f - top) / 30)
            cols, rows = math.ceil((right - src.transform.c) / 30) - col0, math.ceil((src.transform.f - bottom) / 30) - row0
            window = rasterio.windows.Window(col0, row0, cols, rows)
            data = src.read(1, window=window)
            dest = OUT / "cdl" / f"CDL_{year}_{COUNTY_FIPS}_window.tif"
            dest.parent.mkdir(parents=True, exist_ok=True)
            transform = Affine(30, 0, src.transform.c + col0 * 30, 0, -30, src.transform.f - row0 * 30)
            with rasterio.open(dest, "w", driver="GTiff", height=rows, width=cols, count=1, dtype=data.dtype,
                               crs=src.crs, transform=transform, compress="deflate") as out:
                out.write(data, 1)
        entries.append({
            "path": str(dest.relative_to(OUT)), "kind": "cdl-window",
            "derived_from": f"raw/cdl/{cdl.VERSION}/{RAW_DATE}/{src_path.name}",
            "source_sha256": sha256(src_path), "how": "county clip cut to the field window plus 500 m",
        })


def clear_share(fmask_path: Path, field_geom) -> float:
    with rasterio.open(fmask_path) as f:
        geom = gpd.GeoSeries([field_geom], crs=4326).to_crs(f.crs).iloc[0]
        inside = geometry_mask([geom], out_shape=f.shape, transform=f.transform, invert=True)
        fm = f.read(1)
    return float((inside & ((fm & CLEAR_BITS) == 0)).sum() / max(inside.sum(), 1))


def hls_scenes(entries: list[dict]) -> None:
    """Copy four fully clear scenes per sensor, spread over the season, unchanged."""
    field_geom = gpd.read_file(FIELDS_PATH).set_index("field_id").geometry[FIELD]
    for sensor in ("l30", "s30"):
        folder = hls.default_dir() / sensor / FIELD
        clear = {d.name: clear_share(d / "fmask.tif", field_geom) for d in sorted(folder.iterdir())}
        usable = [d for d, share in clear.items() if share >= 0.99]
        chosen = []
        for target in TARGETS:
            best = min((d for d in usable if d not in chosen),
                       key=lambda d: abs((date(int(d[:4]), int(d[4:6]), int(d[6:])) - target).days))
            chosen.append(best)
        for day in chosen:
            for band in hls.BANDS[sensor]:
                src = folder / day / f"{band.lower()}.tif"
                dest = OUT / "hls" / sensor / day / src.name
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dest)
                entries.append({
                    "path": str(dest.relative_to(OUT)), "kind": "hls-window",
                    "derived_from": f"raw/hls/{sensor}/v2.0/{RAW_DATE}/{FIELD}/{day}/{src.name}",
                    "source_sha256": sha256(src), "how": f"copied unchanged; field {clear[day]:.0%} clear",
                })


def power_season(entries: list[dict]) -> None:
    src = power.default_dir() / f"{FIELD}_19910101-20251231.json"
    doc = json.loads(src.read_bytes())
    keep = {name: {d: v for d, v in series.items() if d.startswith(str(SEASON))}
            for name, series in doc["properties"]["parameter"].items()}
    doc["properties"]["parameter"] = keep
    doc["header"]["start"], doc["header"]["end"] = f"{SEASON}0101", f"{SEASON}1231"
    dest = OUT / "power" / f"{FIELD}_{SEASON}0101-{SEASON}1231.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(doc, indent=1, sort_keys=True) + "\n")
    entries.append({
        "path": str(dest.relative_to(OUT)), "kind": "power-season",
        "derived_from": f"raw/power/daily-point-api-v2.10.3/{RAW_DATE}/{src.name}",
        "source_sha256": sha256(src), "how": f"the 1991-2025 response cut to {SEASON}; header otherwise unchanged",
    })


def ssurgo_responses(entries: list[dict]) -> None:
    for src in sorted((ssurgo.default_dir() / FIELD).glob("step_*.json")):
        dest = OUT / "ssurgo" / src.name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
        entries.append({
            "path": str(dest.relative_to(OUT)), "kind": "ssurgo-response",
            "derived_from": f"raw/ssurgo/soil-data-access/{RAW_DATE}/{FIELD}/{src.name}",
            "source_sha256": sha256(src), "how": "copied unchanged",
        })


def main() -> None:
    if OUT.exists():
        shutil.rmtree(OUT)
    entries: list[dict] = []
    cdl_windows(entries)
    hls_scenes(entries)
    power_season(entries)
    ssurgo_responses(entries)
    for entry in entries:
        entry["sample_sha256"] = sha256(OUT / entry["path"])
    manifest = {
        "field_id": FIELD, "season": SEASON, "built": date.today().isoformat(),
        "note": "A small sample for development and tests. It is derived from the raw S3 objects "
                "named in derived_from; raw data is only ever read from S3.",
        "field_bbox_lonlat_500m": list(field_bboxes(gpd.read_file(FIELDS_PATH).query("field_id == @FIELD"), 500)[FIELD]),
        "files": entries,
    }
    (OUT.parent / "sample_manifest.json").write_text(json.dumps(manifest, indent=1) + "\n")
    total = sum((OUT / e["path"]).stat().st_size for e in entries)
    print(f"{len(entries)} files, {total / 1e3:.0f} KB in {OUT.relative_to(ROOT)}")
    kinds = {}
    for e in entries:
        kinds[e["kind"]] = kinds.get(e["kind"], 0) + 1
    print(kinds)


if __name__ == "__main__":
    main()
