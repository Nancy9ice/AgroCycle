"""Checks run on every raw file before it is uploaded: it opens, and it matches the request."""

import json
import zipfile
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

import pandas as pd
import rasterio
from rasterio.warp import transform_bounds
from rasterio.windows import Window


@dataclass
class CheckResult:
    problems: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.problems


def check_opens(path: Path) -> CheckResult:
    """The file exists, is not empty, and can be read by the matching reader."""
    path = Path(path)
    result = CheckResult()
    if not path.exists() or path.stat().st_size == 0:
        result.problems.append(f"{path.name}: missing or empty")
        return result
    suffix = path.suffix.lower()
    try:
        if suffix in (".tif", ".tiff"):
            with rasterio.open(path) as src:
                src.read(1, window=Window(0, 0, min(64, src.width), min(64, src.height)))
        elif suffix == ".csv":
            if pd.read_csv(path, nrows=5).empty:
                result.problems.append(f"{path.name}: no data rows")
        elif suffix == ".json":
            json.loads(path.read_text())
        elif suffix == ".zip":
            with zipfile.ZipFile(path) as archive:
                if (bad := archive.testzip()) is not None:
                    result.problems.append(f"{path.name}: corrupt member {bad}")
    except (OSError, ValueError, rasterio.errors.RasterioError, zipfile.BadZipFile) as err:
        result.problems.append(f"{path.name}: cannot be opened ({err})")
    return result


def check_raster(
    path: Path,
    *,
    crs: str | None = None,
    pixel_size: float | None = None,
    covers: tuple[float, float, float, float] | None = None,
    covers_crs: str = "EPSG:4326",
) -> CheckResult:
    """A raster has the requested CRS and pixel size, and covers the requested bbox."""
    result = check_opens(path)
    if not result.ok:
        return result
    name = Path(path).name
    with rasterio.open(path) as src:
        if crs and src.crs.to_string() != crs:
            result.problems.append(f"{name}: CRS is {src.crs.to_string()}, expected {crs}")
        if pixel_size and abs(src.res[0] - pixel_size) > 1e-6:
            result.problems.append(f"{name}: pixel size is {src.res[0]:g}, expected {pixel_size:g}")
        if covers:
            want = transform_bounds(covers_crs, src.crs, *covers)
            have = src.bounds
            if not (
                have.left <= want[0] and have.bottom <= want[1]
                and have.right >= want[2] and have.top >= want[3]
            ):
                result.problems.append(f"{name}: does not cover the requested bbox")
    return result


def check_dates(found: Iterable[date], start: date, end: date) -> CheckResult:
    """The dates in a file span the requested range."""
    result = CheckResult()
    dates = sorted(found)
    if not dates:
        result.problems.append("no dates found")
    else:
        if dates[0] > start:
            result.problems.append(f"data starts {dates[0]}, requested {start}")
        if dates[-1] < end:
            result.problems.append(f"data ends {dates[-1]}, requested {end}")
    return result
