"""Valid-pixel counts per window: the denominators for everything DS1 computes from HLS.

Pixels are those whose centre lies in the field polygon. Every pixel is exactly one of fill (no data),
flagged (masked by bits 1-5 of Fmask) or valid, so total = fill + flagged + valid.
"""

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass

import pandas as pd

from ingest.hls import is_no_data
from transform.field_schema import load_fields
from transform.hls import mask
from transform.hls.sources import NO_DATA_KEY, Window

WORKERS = 8
COLUMNS = ["field_id", "sensor", "acquired", "sensing_time", "status", "total_pixels", "fill_pixels",
           "flagged_pixels", "valid_pixels", "valid_share", "mask_rule", "source_s3_key"]


@dataclass(frozen=True)
class Counts:
    total: int
    fill: int
    flagged: int
    valid: int
    no_data: bool  # the whole window is fill (the pattern Phase 1 listed instead of uploading)


def field_polygons() -> dict:
    """Each field's polygon in the tile CRS (EPSG:32615), from the validated field file."""
    fields = load_fields().to_crs(mask.TILE_CRS)
    return dict(zip(fields["field_id"], fields.geometry, strict=True))


def count_stack(stack: mask.Stack, polygon) -> Counts:
    classes = mask.classify(stack.data)
    inside = mask.inside_polygon(stack.data.shape[1:], stack.transform, polygon)
    fill, flagged, valid = (int((x & inside).sum()) for x in (classes.fill, classes.flagged, classes.valid))
    return Counts(int(inside.sum()), fill, flagged, valid, is_no_data(stack.data))


def _row(window: Window, counts: Counts, source_key: str) -> dict:
    return {
        "field_id": window.field_id, "sensor": window.sensor, "acquired": pd.Timestamp(window.acquired),
        "sensing_time": window.sensing_time, "status": "no_data" if counts.no_data else "observed",
        "total_pixels": counts.total, "fill_pixels": counts.fill, "flagged_pixels": counts.flagged,
        "valid_pixels": counts.valid, "valid_share": counts.valid / counts.total if counts.total else 0.0,
        "mask_rule": mask.MASK_RULE, "source_s3_key": source_key,
    }


def count_windows(source, polygons: dict | None = None) -> pd.DataFrame:
    """One row per window: every stack the source holds, plus the windows it only lists (no file)."""
    polygons = polygons or field_polygons()
    windows = source.windows()

    def one(window: Window) -> dict:
        return _row(window, count_stack(source.read(window), polygons[window.field_id]), window.s3_key)

    with ThreadPoolExecutor(WORKERS) as pool:
        rows = list(pool.map(one, windows))
    listed = source.no_data_windows()
    if listed:
        # no file to read: the polygon's pixel count comes from the grid of a sibling stack of the same field
        grid = {}
        for window in listed:
            if window.field_id not in grid:
                sibling = next(w for w in windows if w.field_id == window.field_id)
                stack = source.read(sibling)
                grid[window.field_id] = int(mask.inside_polygon(
                    stack.data.shape[1:], stack.transform, polygons[window.field_id]).sum())
            total = grid[window.field_id]
            rows.append(_row(window, Counts(total, total, 0, 0, True), NO_DATA_KEY))
    frame = pd.DataFrame(rows, columns=COLUMNS)
    return frame.sort_values(["field_id", "acquired", "sensor", "sensing_time"]).reset_index(drop=True)

