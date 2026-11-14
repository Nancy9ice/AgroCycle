"""Count CDL classes inside a field polygon.

A pixel belongs to the field when its centre lies inside the polygon (rasterio's default, not
`all_touched`). A 20-40 ha field covers a few hundred 30 m pixels, so pixels on the edge move a
share by a point or two; that is a property of the method, recorded in the Phase 3 spec.
"""

from collections import Counter
from dataclasses import dataclass
from pathlib import Path

import geopandas as gpd
import numpy as np
import rasterio
from rasterio.features import geometry_window, rasterize
from shapely.geometry import mapping

from ingest.cdl import RESAMPLED_YEARS, SOURCE, VERSION, find_files, retrieval_date
from ingest.s3_store import raw_key

RESOLUTION_M = 30
RASTER_CRS = "EPSG:5070"


@dataclass(frozen=True)
class Clip:
    county: str
    year: int
    path: Path
    resolution_m: int
    product_version: str
    s3_key: str


def clips(base: Path) -> dict[tuple[str, int], Clip]:
    """Every county clip under `base` (the CDL pull folder), with the provenance each row needs."""
    found = {}
    for (county, year), path in find_files(base).items():
        note = "; resampled to 30 m from the native 10 m product" if year in RESAMPLED_YEARS else ""
        found[(county, year)] = Clip(
            county, year, path, RESOLUTION_M, f"CDL {year} ({VERSION}){note}",
            raw_key(SOURCE, VERSION, retrieval_date(path), path.name),
        )
    return found


def class_names(clip_path: Path) -> dict[int, str]:
    """Code to crop name, from the class table that came with the clip."""
    table = clip_path.with_name(clip_path.name + ".vat.dbf")
    frame = gpd.read_file(table)
    return {int(row.VALUE): str(row.CLASS_NAME) for row in frame.itertuples()}


def field_counts(raster: Path, geometry) -> Counter:
    """Pixels per CDL class whose centre is inside `geometry` (already in the raster's CRS)."""
    with rasterio.open(raster) as src:
        if src.crs.to_string() != RASTER_CRS:
            raise ValueError(f"{raster.name}: CRS {src.crs}, expected {RASTER_CRS}")
        left, bottom, right, top = geometry.bounds
        b = src.bounds
        if left < b.left or bottom < b.bottom or right > b.right or top > b.top:
            raise ValueError(f"{raster.name}: the field is not inside the clip")
        window = geometry_window(src, [mapping(geometry)])
        data = src.read(1, window=window)
        transform = src.window_transform(window)
    inside = rasterize(
        [(mapping(geometry), 1)], out_shape=data.shape, transform=transform,
        fill=0, all_touched=False, dtype="uint8",
    ).astype(bool)
    codes, counts = np.unique(data[inside], return_counts=True)
    return Counter({int(code): int(count) for code, count in zip(codes, counts, strict=True)})
