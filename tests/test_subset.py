import geopandas as gpd
import pytest

from ingest.subset import (
    SizeBudgetExceededError,
    check_budget,
    county_bboxes,
    field_bboxes,
    field_points,
    subset_record,
    union_bbox,
)
from transform.field_schema import FIELDS_PATH

FIELDS = gpd.read_file(FIELDS_PATH)


def test_one_bbox_per_field_and_the_buffer_grows_it():
    plain, grown = field_bboxes(FIELDS), field_bboxes(FIELDS, buffer_m=500)
    assert len(plain) == len(FIELDS) == 45
    for fid, (minx, miny, maxx, maxy) in plain.items():
        gx0, gy0, gx1, gy1 = grown[fid]
        assert gx0 < minx and gy0 < miny and gx1 > maxx and gy1 > maxy


def test_each_field_bbox_contains_its_field():
    boxes = field_bboxes(FIELDS)
    for row in FIELDS.itertuples():
        minx, miny, maxx, maxy = boxes[row.field_id]
        bx0, by0, bx1, by1 = row.geometry.bounds
        tol = 1e-5  # the bbox is rounded to 6 decimals
        assert minx <= bx0 + tol and miny <= by0 + tol
        assert maxx >= bx1 - tol and maxy >= by1 - tol


def test_points_fall_inside_their_fields():
    points = field_points(FIELDS)
    for row in FIELDS.itertuples():
        lon, lat = points[row.field_id]
        assert row.geometry.buffer(1e-5).contains(gpd.points_from_xy([lon], [lat])[0])


def test_union_bbox_covers_every_field_bbox():
    minx, miny, maxx, maxy = union_bbox(FIELDS, buffer_m=500)
    for fx0, fy0, fx1, fy1 in field_bboxes(FIELDS, buffer_m=500).values():
        assert minx <= fx0 and miny <= fy0 and maxx >= fx1 and maxy >= fy1


def test_county_bboxes_are_in_the_cdl_grid():
    boxes = county_bboxes()
    assert set(boxes) == {"Story", "Boone"}
    assert 150_000 < boxes["Boone"][0] < 230_000  # EPSG:5070 metres, matching the clips


def test_budget_check_and_subset_record():
    check_budget("cdl", 38_000_000, 100_000_000)
    with pytest.raises(SizeBudgetExceededError):
        check_budget("cdl", 120_000_000, 100_000_000)
    assert subset_record("county", counties=["Story"]) == {"kind": "county", "counties": ["Story"]}
