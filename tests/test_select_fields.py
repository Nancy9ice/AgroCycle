"""Checks the CDL loader on small synthetic rasters, including mixed 30 m and 10 m years."""

import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin

from scripts import select_fields as sf


def _write(path, array, res, left, top):
    path.parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(
        path, "w", driver="GTiff", height=array.shape[0], width=array.shape[1], count=1,
        dtype="uint8", crs="EPSG:5070", transform=from_origin(left, top, res, res),
    ) as dst:
        dst.write(array, 1)


@pytest.fixture
def clips(tmp_path, monkeypatch):
    monkeypatch.setattr(sf, "CDL_DIR", tmp_path)
    monkeypatch.setattr(sf, "YEARS", [2023, 2024])
    monkeypatch.setitem(sf.FIPS, "Test", "99999")
    return tmp_path / "polygonclip_a"


def test_mixed_resolutions_share_one_fine_grid(clips):
    coarse = np.array([[1, 5], [5, 1]], np.uint8)  # 30 m, 2 x 2 pixels
    fine = np.repeat(np.repeat(coarse, 3, 0), 3, 1)  # 10 m, 6 x 6 pixels
    fine[0, 0] = 176
    _write(clips / "CDL_2023_99999.tif", coarse, 30, 1005, 2065)
    _write(clips / "CDL_2024_99999.tif", fine, 10, 1005, 2065)

    groups, origin, res = sf.load_county("Test")

    assert res == 10 and origin == (1005, 2065) and groups.shape == (2, 6, 6)
    assert (groups[0] == sf.LUT[np.repeat(np.repeat(coarse, 3, 0), 3, 1)]).all()
    assert groups[1][0, 0] == sf.GRASS and groups[1][0, 1] == sf.CORN


def test_years_on_slightly_different_extents_are_cropped_to_the_common_area(clips):
    wide = np.full((4, 4), 1, np.uint8)  # one extra row and column, like the Boone files
    narrow = np.full((3, 3), 5, np.uint8)
    _write(clips / "CDL_2023_99999.tif", wide, 30, 975, 2095)  # starts 30 m further out
    _write(clips / "CDL_2024_99999.tif", narrow, 30, 1005, 2065)

    groups, origin, res = sf.load_county("Test")

    assert res == 30 and origin == (1005, 2065) and groups.shape == (2, 3, 3)
    assert (groups[0] == sf.CORN).all() and (groups[1] == sf.SOY).all()


def test_misaligned_grids_are_rejected(clips):
    coarse = np.ones((2, 2), np.uint8)
    fine = np.ones((6, 6), np.uint8)
    _write(clips / "CDL_2023_99999.tif", coarse, 30, 1005, 2065)
    _write(clips / "CDL_2024_99999.tif", fine, 10, 1000, 2065)  # 5 m off the other grid

    with pytest.raises(RuntimeError, match="not aligned"):
        sf.load_county("Test")
