"""Offline checks that the selection notes agree with the committed field file.

These need no CDL clips. The raster-based check is scripts/verify_fields.py.
"""

from itertools import pairwise

import geopandas as gpd
import pandas as pd
import pytest

from scripts.select_fields import CLASS_TO_NOTE, LETTERS, YEARS, cover_detail
from transform.field_schema import FIELDS_PATH, ROOT

NOTES = ROOT / "data" / "fields" / "field_selection_notes.csv"
SEQUENCE = f"crops_{YEARS[0]}_{YEARS[-1]}"

pytestmark = pytest.mark.skipif(
    not (FIELDS_PATH.exists() and NOTES.exists()), reason="field files not generated yet"
)


def _alternations(seq: str) -> int:
    return sum(a != b and a in "CS" and b in "CS" for a, b in pairwise(seq))


@pytest.fixture(scope="module")
def joined():
    fields = gpd.read_file(FIELDS_PATH)
    notes = pd.read_csv(NOTES)
    return fields.set_index("field_id"), notes.set_index("field_id")


def test_notes_cover_exactly_the_fields(joined):
    fields, notes = joined
    assert set(fields.index) == set(notes.index)


def test_class_county_and_area_match_the_field_file(joined):
    fields, notes = joined
    area_ha = fields.to_crs(5070).area / 10_000
    for fid, row in notes.iterrows():
        assert fields.loc[fid, "domain_note"] == CLASS_TO_NOTE[row.cdl_class], fid
        assert fields.loc[fid, "county"] == row.county, fid
        assert abs(area_ha[fid] - row.area_ha) / row.area_ha < 0.01, fid


def test_crop_sequences_follow_the_class_rules(joined):
    _, notes = joined
    for fid, row in notes.iterrows():
        seq = row[SEQUENCE]
        assert len(seq) == len(YEARS) and set(seq) <= set(LETTERS[1:]), fid
        if row.cdl_class == "rotation":
            assert set(seq) <= set("CS") and _alternations(seq) >= len(YEARS) - 2, fid
        elif row.cdl_class == "corn":
            assert seq.count("C") >= len(YEARS) - 1, fid
        elif row.cdl_class == "pasture":
            assert sum(seq.count(letter) for letter in "GAH") >= len(YEARS) - 2, fid
        else:
            assert seq.count("C") + seq.count("S") >= 5, fid


def test_cover_detail_matches_the_sequence(joined):
    fields, notes = joined
    for fid, row in notes.iterrows():
        expected = cover_detail(row.cdl_class, row[SEQUENCE])
        in_geojson = fields.loc[fid, "cover_detail"]
        in_notes = row.cover_detail
        if expected is None:
            assert pd.isna(in_geojson) and pd.isna(in_notes), fid
        else:
            assert in_geojson == expected == in_notes, fid


def test_primary_field_alternates_every_year(joined):
    fields, notes = joined
    (primary,) = fields.index[fields["role"] == "primary"]
    seq = notes.loc[primary, SEQUENCE]
    assert set(seq) <= set("CS") and _alternations(seq) == len(YEARS) - 1
