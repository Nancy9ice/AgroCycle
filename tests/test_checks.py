import json
import zipfile
from datetime import date

import numpy as np
import rasterio
from rasterio.transform import from_origin

from ingest.checks import check_dates, check_opens, check_raster


def _raster(path, res=30.0, left=188745.0, top=2137605.0, size=10, crs="EPSG:5070"):
    with rasterio.open(
        path, "w", driver="GTiff", height=size, width=size, count=1, dtype="uint8",
        crs=crs, transform=from_origin(left, top, res, res),
    ) as dst:
        dst.write(np.ones((size, size), np.uint8), 1)
    return path


def test_valid_raster_passes_all_checks(tmp_path):
    path = _raster(tmp_path / "a.tif")
    # a small bbox in Story County, well inside the raster
    result = check_raster(
        path, crs="EPSG:5070", pixel_size=30, covers=(188800, 2137400, 188900, 2137500),
        covers_crs="EPSG:5070",
    )
    assert result.ok, result.problems


def test_wrong_crs_pixel_size_and_coverage_are_reported(tmp_path):
    path = _raster(tmp_path / "a.tif", res=10.0)
    result = check_raster(
        path, crs="EPSG:4326", pixel_size=30, covers=(0, 0, 1000, 1000), covers_crs="EPSG:5070"
    )
    text = " ".join(result.problems)
    assert "CRS" in text and "pixel size" in text and "does not cover" in text


def test_missing_empty_and_corrupt_files_fail_to_open(tmp_path):
    empty = tmp_path / "empty.csv"
    empty.write_bytes(b"")
    corrupt = tmp_path / "bad.tif"
    corrupt.write_bytes(b"not a raster")
    assert not check_opens(tmp_path / "missing.csv").ok
    assert not check_opens(empty).ok
    assert not check_opens(corrupt).ok


def test_csv_json_and_zip_files_open(tmp_path):
    csv = tmp_path / "a.csv"
    csv.write_text("a,b\n1,2\n")
    js = tmp_path / "a.json"
    js.write_text(json.dumps({"ok": True}))
    zp = tmp_path / "a.zip"
    with zipfile.ZipFile(zp, "w") as archive:
        archive.writestr("x.txt", "hello")
    assert check_opens(csv).ok and check_opens(js).ok and check_opens(zp).ok


def test_csv_with_only_a_header_fails(tmp_path):
    csv = tmp_path / "a.csv"
    csv.write_text("a,b\n")
    assert not check_opens(csv).ok


def test_date_range_must_span_the_request():
    found = [date(2020, 1, 1), date(2020, 12, 31)]
    assert check_dates(found, date(2020, 1, 1), date(2020, 12, 31)).ok
    late = check_dates(found, date(2019, 1, 1), date(2021, 1, 1))
    assert len(late.problems) == 2
    assert not check_dates([], date(2020, 1, 1), date(2020, 12, 31)).ok
