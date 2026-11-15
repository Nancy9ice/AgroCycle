"""Valid-pixel counts per window: the denominators for everything DS1 computes from HLS.

Pixels are those whose centre lies in the field polygon. Every pixel is exactly one of fill (no data),
flagged (masked by bits 1-5 of Fmask) or valid, so total = fill + flagged + valid.

A window is `no_data` when every pixel of the field is fill: the satellite has nothing over the field, even
if the window's 500 m buffer holds data. That is no observation, never clear and never cloudy. It includes
the 1,962 windows Phase 1 listed instead of uploading (all fill over the whole window) and any other window
whose data stops short of the field.
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
    window_no_data: bool  # fill over the whole window: the pattern Phase 1 listed instead of uploading

    @property
    def no_data(self) -> bool:
        """Every pixel of the field is fill (and the field has pixels)."""
        return self.total > 0 and self.fill == self.total


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
    if counts.total == 0:
        raise ValueError(
            f"{window.field_id}: the polygon holds no pixel centre in the {window.sensor} window of "
            f"{window.acquired}, so no count is possible"
        )
    return {
        "field_id": window.field_id, "sensor": window.sensor, "acquired": pd.Timestamp(window.acquired),
        "sensing_time": window.sensing_time, "status": "no_data" if counts.no_data else "observed",
        "total_pixels": counts.total, "fill_pixels": counts.fill, "flagged_pixels": counts.flagged,
        "valid_pixels": counts.valid, "valid_share": counts.valid / counts.total,
        "mask_rule": mask.MASK_RULE, "source_s3_key": source_key,
    }


def _key(window: Window) -> tuple:
    return (window.field_id, window.sensor, window.acquired, window.sensing_time)


def count_windows(source, polygons: dict | None = None) -> pd.DataFrame:
    """One row per window: every stack the source holds, plus the windows it only lists (no file).

    A stack whose window is all fill was never uploaded (Phase 1 listed it instead), so its source key is
    the list's key, the same whether the stack was read locally or the window came from the list.
    """
    polygons = polygons or field_polygons()
    windows = source.windows()
    missing = sorted({w.field_id for w in windows} - set(polygons))
    if missing:
        raise ValueError(f"stacks for fields that are not in the field file: {', '.join(missing)}")

    def one(window: Window) -> dict:
        found = count_stack(source.read(window), polygons[window.field_id])
        return _row(window, found, NO_DATA_KEY if found.window_no_data else window.s3_key)

    with ThreadPoolExecutor(WORKERS) as pool:
        rows = list(pool.map(one, windows))

    listed = source.no_data_windows()
    if listed:
        clash = {_key(w) for w in listed} & {_key(w) for w in windows}
        if clash:
            raise ValueError(
                f"{len(clash)} windows are both stored and listed as having no data, for example {min(clash)}"
            )
        # no file to read: the polygon's pixel count comes from the grid of a sibling stack of the same field
        grid = {}
        for window in listed:
            if window.field_id not in polygons:
                raise ValueError(f"{window.field_id} is listed as having no data but is not in the field file")
            if window.field_id not in grid:
                sibling = next((w for w in windows if w.field_id == window.field_id), None)
                if sibling is None:
                    raise ValueError(f"{window.field_id}: no stack to take the pixel grid from for its no-data windows")
                stack = source.read(sibling)
                grid[window.field_id] = int(mask.inside_polygon(
                    stack.data.shape[1:], stack.transform, polygons[window.field_id]).sum())
            total = grid[window.field_id]
            rows.append(_row(window, Counts(total, total, 0, 0, True), NO_DATA_KEY))
    frame = pd.DataFrame(rows, columns=COLUMNS)
    return frame.sort_values(["field_id", "acquired", "sensor", "sensing_time"]).reset_index(drop=True)
