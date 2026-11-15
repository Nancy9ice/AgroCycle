from datetime import date

import geopandas as gpd
import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin
from rasterio.warp import transform_bounds
from shapely.geometry import box

from ingest import naip
from ingest.subset import SizeBudgetExceededError

CRS = "EPSG:26915"
ORIGIN_X, ORIGIN_Y, RES, SIZE = 450_000.0, 4_650_000.0, 0.6, 1000  # a 600 m tile


def _tile_file(path, x0, value):
    """A 4-band uint8 tile of one constant value, 600 m wide, upper-left corner at x0."""
    data = np.full((4, SIZE, SIZE), value, dtype="uint8")
    with rasterio.open(path, "w", driver="GTiff", height=SIZE, width=SIZE, count=4, dtype="uint8",
                       crs=CRS, transform=from_origin(x0, ORIGIN_Y, RES, RES)) as dst:
        dst.write(data)
    return path


def _lonlat_box(x0, x1, y0=ORIGIN_Y - 400, y1=ORIGIN_Y - 100):
    return transform_bounds(CRS, "EPSG:4326", x0, y0, x1, y1)


def _tile(item_id, path, day=13):
    return naip.Tile(item_id, str(path), date(2025, 8, day), (0, 0, 0, 0))


def test_a_field_inside_one_tile_is_cut_from_that_tile(tmp_path):
    left = _tile_file(tmp_path / "a.tif", ORIGIN_X, 10)
    bbox = _lonlat_box(ORIGIN_X + 100, ORIGIN_X + 300)
    out = tmp_path / "chip.tif"
    used = naip.clip_chip([_tile("a", left)], bbox, out, token=None)
    assert used["tiles"] == ["a"] and naip.check_chip(out, bbox).ok


def test_a_field_across_two_tiles_is_placed_correctly(tmp_path):
    """Regression: the second tile's pixels were placed with the wrong transform, leaving the chip short."""
    left = _tile_file(tmp_path / "a.tif", ORIGIN_X, 10)
    right = _tile_file(tmp_path / "b.tif", ORIGIN_X + SIZE * RES, 20)
    edge = ORIGIN_X + SIZE * RES
    bbox = _lonlat_box(edge - 150, edge + 150)  # 300 m wide, centred on the seam
    out = tmp_path / "chip.tif"
    used = naip.clip_chip([_tile("a", left), _tile("b", right)], bbox, out, token=None)
    assert used["tiles"] == ["a", "b"]
    assert naip.check_chip(out, bbox).ok
    with rasterio.open(out) as src:
        values = {int(src.read(1)[row, col]) for row in (5, src.height // 2) for col in (5, src.width - 5)}
        assert values == {10, 20}  # left edge from tile a, right edge from tile b
        assert src.sample([(edge - 50, ORIGIN_Y - 250)]).__next__()[0] == 10
        assert src.sample([(edge + 50, ORIGIN_Y - 250)]).__next__()[0] == 20


def test_a_tile_that_touches_the_search_box_but_adds_no_pixels_is_not_listed(tmp_path):
    left = _tile_file(tmp_path / "a.tif", ORIGIN_X, 10)
    far = _tile_file(tmp_path / "far.tif", ORIGIN_X + 5000, 99)
    bbox = _lonlat_box(ORIGIN_X + 100, ORIGIN_X + 300)
    used = naip.clip_chip([_tile("a", left), _tile("far", far)], bbox, tmp_path / "chip.tif", token=None)
    assert used["tiles"] == ["a"]


def test_check_chip_rejects_an_empty_or_short_chip(tmp_path):
    left = _tile_file(tmp_path / "a.tif", ORIGIN_X, 0)
    bbox = _lonlat_box(ORIGIN_X + 100, ORIGIN_X + 300)
    out = tmp_path / "blank.tif"
    naip.clip_chip([_tile("a", left)], bbox, out, token=None)
    assert any("every pixel is 0" in p for p in naip.check_chip(out, bbox).problems)
    wider = _lonlat_box(ORIGIN_X + 100, ORIGIN_X + 900)
    assert any("does not cover" in p for p in naip.check_chip(out, wider).problems)


def _fields():
    return gpd.GeoDataFrame({"field_id": ["f1"], "geometry": [box(-93.60, 42.00, -93.598, 42.002)]}, crs=4326)


def test_plan_makes_one_item_per_field_with_dates_and_no_token(tmp_path):
    src = _tile_file(tmp_path / "src.tif", ORIGIN_X, 50)
    fields = _fields()
    left, bottom, right, top = transform_bounds("EPSG:4326", CRS, *fields.total_bounds)

    def searcher(bbox, year):
        return [naip.Tile("tile-1", str(src), date(2025, 8, 13), (0, 0, 0, 0))]

    def clipper(tiles, bbox, dest, token):  # the field is far from the synthetic tile, so cut a fixed box
        return naip.clip_chip(tiles, _lonlat_box(ORIGIN_X + 100, ORIGIN_X + 300), dest, None)

    items = naip.plan(tmp_path / "out", searcher, clipper, token="SECRET-TOKEN", fields=fields)
    item = items[0]
    assert item.manifest.evidence_type == "observed" and item.manifest.subset["flight_dates"] == ["2025-08-13"]
    assert "SECRET-TOKEN" not in item.manifest.to_json() and "sig=" not in item.manifest.to_json()
    assert item.manifest.subset["tiles"] == ["tile-1"] and left < right and bottom < top


def test_a_saved_chip_keeps_the_tiles_it_was_cut_from_and_needs_no_network(tmp_path, monkeypatch):
    """A rerun must not list a candidate tile that gave no pixels, and must not search or fetch a token."""
    a = _tile_file(tmp_path / "a.tif", ORIGIN_X, 10)
    unused = _tile_file(tmp_path / "unused.tif", ORIGIN_X + 5000, 99)
    cut_box = _lonlat_box(ORIGIN_X + 100, ORIGIN_X + 300)
    tiles = [_tile("tile_a_20250813", a), _tile("tile_unused_20250805", unused, day=5)]

    def clipper(tiles, bbox, dest, token):
        return naip.clip_chip(tiles, cut_box, dest, None)

    first = naip.plan(tmp_path / "out", lambda b, y: tiles, clipper, token="t", fields=_fields())
    assert first[0].manifest.subset["tiles"] == ["tile_a_20250813"]

    def no_network(*args, **kwargs):
        raise AssertionError("a saved chip must not search or ask for a token")

    monkeypatch.setattr(naip, "access_token", no_network)
    again = naip.plan(tmp_path / "out", no_network, no_network, fields=_fields())
    assert again[0].manifest.subset["tiles"] == ["tile_a_20250813"]
    assert again[0].manifest.subset["flight_dates"] == ["2025-08-13"]


def test_a_chip_without_its_tile_record_is_cut_again(tmp_path):
    src = _tile_file(tmp_path / "src.tif", ORIGIN_X, 50)
    calls = []

    def clipper(tiles, bbox, dest, token):
        calls.append(dest.name)
        return naip.clip_chip(tiles, _lonlat_box(ORIGIN_X + 100, ORIGIN_X + 300), dest, None)

    kwargs = {"token": "t", "fields": _fields()}
    naip.plan(tmp_path / "out", lambda b, y: [_tile("t1", src)], clipper, **kwargs)
    (tmp_path / "out" / f"f1_naip2025.tif{naip.TILES_RECORD}").unlink()
    naip.plan(tmp_path / "out", lambda b, y: [_tile("t1", src)], clipper, **kwargs)
    assert len(calls) == 2


def test_only_the_first_covering_tile_is_opened(tmp_path, monkeypatch):
    a = _tile_file(tmp_path / "a.tif", ORIGIN_X, 10)
    b = _tile_file(tmp_path / "b.tif", ORIGIN_X, 20)  # also covers, but need not be opened
    opened = []
    real_open = rasterio.open

    def counting_open(path, *args, **kwargs):
        if str(path).endswith(("a.tif", "b.tif")) and not args:
            opened.append(str(path).rsplit("/", 1)[1])
        return real_open(path, *args, **kwargs)

    monkeypatch.setattr(naip.rasterio, "open", counting_open)
    naip.clip_chip([_tile("b", b), _tile("a", a)], _lonlat_box(ORIGIN_X + 100, ORIGIN_X + 300),
                   tmp_path / "chip.tif", token=None)
    assert opened == ["a.tif"]  # tiles are tried in id order and the first cover stops the search


def test_flight_date_comes_from_the_tile_id():
    assert naip.flight_date_from_id("ia_m_4209358_se_15_060_20250813") == date(2025, 8, 13)
    with pytest.raises(ValueError):
        naip.flight_date_from_id("not-a-tile")


def test_a_field_with_no_tile_is_reported_not_skipped_silently(tmp_path):
    items = naip.plan(tmp_path, lambda b, y: [], lambda *a: {}, token="t", fields=_fields())
    assert not items[0].checks.ok and "no NAIP" in items[0].checks.problems[0]


def test_budget_is_enforced(tmp_path, monkeypatch):
    src = _tile_file(tmp_path / "src.tif", ORIGIN_X, 50)
    monkeypatch.setattr(naip, "BUDGET_BYTES", 10)
    with pytest.raises(SizeBudgetExceededError):
        naip.plan(tmp_path / "out", lambda b, y: [_tile("t", src)],
                  lambda tiles, bbox, dest, token: naip.clip_chip(
                      tiles, _lonlat_box(ORIGIN_X + 100, ORIGIN_X + 300), dest, None),
                  token="t", fields=_fields())
