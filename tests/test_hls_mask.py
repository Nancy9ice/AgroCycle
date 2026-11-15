"""The Fmask rule, fill, scaling and polygon clip, tested bit by bit and on the committed primary-001 scenes."""

from pathlib import Path

import numpy as np
import pytest
import rasterio
import shapely
from rasterio.transform import from_origin
from shapely.geometry import box

from transform.hls import mask

SAMPLE = Path(__file__).resolve().parent.parent / "data" / "sample" / "primary-001" / "hls"
TF = from_origin(500000, 4650000, 30, 30)


def stack(fmask, reflectance=500, shape=None):
    """A 3-reflectance-band stack whose Fmask band holds `fmask` (a scalar or an array)."""
    fmask = np.asarray(fmask, dtype=np.int16)
    shape = fmask.shape if fmask.ndim == 2 else shape
    bands = np.full((3, *shape), reflectance, dtype=np.int16)
    last = np.broadcast_to(fmask, shape).astype(np.int16)[None]
    return mask.Stack(np.concatenate([bands, last]), TF, mask.TILE_CRS)


def expected_valid(value: int) -> bool:
    """The rule, written out on one Python int."""
    return value != 255 and all(not (value >> bit) & 1 for bit in (1, 2, 3, 4, 5))


def test_all_256_fmask_values_follow_the_rule():
    values = np.arange(256, dtype=np.int16).reshape(16, 16)
    classes = mask.classify(stack(values).data)
    for value in range(256):
        row, col = divmod(value, 16)
        assert bool(classes.valid[row, col]) == expected_valid(value), value
        assert bool(classes.fill[row, col]) == (value == 255), value
        assert bool(classes.flagged[row, col]) == (value != 255 and not expected_valid(value)), value


@pytest.mark.parametrize("bit", [1, 2, 3, 4, 5])
def test_bits_1_to_5_each_mask_a_pixel(bit):
    assert not mask.classify(stack(1 << bit, shape=(2, 2)).data).valid.any()


@pytest.mark.parametrize("value", [0, 1, 64, 128, 192, 193])
def test_cirrus_and_aerosol_bits_do_not_mask(value):
    """Bit 0 (cirrus, unused) and bits 6-7 (aerosol level) are kept: only the cloud-family bits mask."""
    assert mask.classify(stack(value, shape=(2, 2)).data).valid.all()


def test_the_real_cloud_with_high_aerosol_value_194_is_masked_and_aerosol_only_64_is_kept():
    classes = mask.classify(stack([[194, 64], [196, 128]]).data)
    assert classes.valid.tolist() == [[False, True], [False, True]]


def test_every_pixel_is_exactly_one_of_fill_flagged_or_valid():
    classes = mask.classify(stack(np.arange(256, dtype=np.int16).reshape(16, 16)).data)
    total = classes.fill.astype(int) + classes.flagged.astype(int) + classes.valid.astype(int)
    assert (total == 1).all()


def test_a_reflectance_fill_value_is_fill_whatever_fmask_says():
    data = stack(0, shape=(2, 2)).data.copy()
    data[1, 0, 0] = mask.REFLECTANCE_FILL  # one band of one pixel
    classes = mask.classify(data)
    assert classes.fill.tolist() == [[True, False], [False, False]]
    assert not classes.valid[0, 0] and classes.valid[1, 1]


def test_scaling_keeps_small_negative_reflectance_and_turns_fill_into_nan_not_zero():
    data = stack(0, shape=(2, 2)).data.copy()
    data[0] = [[1234, -50], [mask.REFLECTANCE_FILL, 0]]
    out = mask.masked_reflectance(mask.Stack(data, TF, mask.TILE_CRS)).reflectance[0]
    assert out[0, 0] == pytest.approx(0.1234) and out[0, 1] == pytest.approx(-0.005)  # a negative is data
    assert np.isnan(out[1, 0])  # fill is null
    assert out[1, 1] == 0.0  # a real zero stays zero
    assert out.dtype == np.float32


def test_masked_pixels_are_nan_in_every_band():
    out = mask.masked_reflectance(stack([[2, 0]], shape=(1, 2))).reflectance
    assert np.isnan(out[:, 0, 0]).all() and not np.isnan(out[:, 0, 1]).any()


def test_pixels_outside_the_polygon_are_nan_and_the_centre_rule_decides_the_edge():
    full = stack(0, shape=(4, 4))
    polygon = box(500030, 4649880, 500090, 4649970)  # x 30-90 m, y from the top 30-120 m: columns 1-2, rows 1-3
    result = mask.masked_reflectance(full, polygon)
    assert result.inside.sum() == 6 and np.isfinite(result.reflectance[0]).sum() == 6
    assert np.isnan(result.reflectance[0][0]).all()  # the top row is outside
    narrower = box(500030, 4649880, 500074, 4649970)  # ends at 74 m: the centre of column 2 (75 m) is out
    assert mask.masked_reflectance(full, narrower).inside.sum() == 3


def test_a_wrong_crs_or_dtype_is_refused(tmp_path):
    path = tmp_path / "wrong.tif"
    with rasterio.open(path, "w", driver="GTiff", height=2, width=2, count=4, dtype="int16", crs="EPSG:4326",
                       transform=from_origin(0, 2, 1, 1)) as out:
        out.write(np.zeros((4, 2, 2), dtype="int16"))
    with pytest.raises(ValueError, match="CRS"):
        mask.read_stack(path)


def sample_stack(date="20230413", sensor="l30"):
    folder = SAMPLE / sensor / date
    bands = []
    for name in ("b04", "b05", "b06", "fmask") if sensor == "l30" else ("b04", "b8a", "b11", "fmask"):
        with rasterio.open(folder / f"{name}.tif") as src:
            bands.append(src.read(1).astype("int16"))
            transform, crs = src.transform, src.crs.to_string()
    return mask.Stack(np.stack(bands), transform, crs)


def independent_counts(stack_, polygon):
    """A recount that shares no code with mask.py: shapely centres and per-pixel Python integers."""
    rows, cols = stack_.data.shape[1:]
    fill = flagged = valid = total = 0
    for r in range(rows):
        for c in range(cols):
            x, y = stack_.transform @ (c + 0.5, r + 0.5)
            if not shapely.contains_xy(polygon, x, y):
                continue
            total += 1
            f = int(stack_.data[-1, r, c])
            if f == 255 or any(int(stack_.data[b, r, c]) == -9999 for b in range(stack_.data.shape[0] - 1)):
                fill += 1
            elif f & 0b00111110:
                flagged += 1
            else:
                valid += 1
    return total, fill, flagged, valid


@pytest.mark.skipif(not (SAMPLE / "l30").exists(), reason="the dev sample is not here")
def test_the_primary_field_sample_scenes_match_an_independent_recount():
    from transform.hls.counts import count_stack, field_polygons

    polygon = field_polygons()["primary-001"]
    seen = 0
    for sensor in ("l30", "s30"):
        for folder in sorted((SAMPLE / sensor).iterdir()):
            scene = sample_stack(folder.name, sensor)
            counts = count_stack(scene, polygon)
            assert (counts.total, counts.fill, counts.flagged, counts.valid) == independent_counts(scene, polygon)
            seen += 1
    assert seen == 8  # the four clear Landsat and four clear Sentinel-2 scenes
