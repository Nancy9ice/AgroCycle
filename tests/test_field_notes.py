"""Offline checks that the selection notes agree with the committed field file.

These need no CDL clips. The raster-based check is scripts/verify_fields.py.
"""

from itertools import pairwise

import geopandas as gpd
import pandas as pd
import pytest

from scripts.select_fields import CLASS_TO_NOTE, YEARS
from transform.field_schema import FIELDS_PATH, ROOT

NOTES = ROOT / "data" / "fields" / "field_selection_notes.csv"

pytestmark = pytest.mark.skipif(
    not (FIELDS_PATH.exists() and NOTES.exists()), reason="field files not generated yet"
)


def _alternations(seq: str) -> int:
    return sum(a != b and a in "CS" and b in "CS" for a, b in pairwise(seq))


@pytest.fixture(scope="module")
def joined():
    fields = gpd.read_file(FIELDS_PATH)
    notes = pd.read_csv(NOTES).set_index("field_id")
    return fields.set_index("field_id"), notes


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
    column = f"crops_{YEARS[0]}_{YEARS[-1]}"
    for fid, row in notes.iterrows():
        seq = row[column]
        assert len(seq) == len(YEARS) and set(seq) <= set("CSPO"), fid
        if row.cdl_class == "rotation":
            assert set(seq) <= set("CS") and _alternations(seq) >= len(YEARS) - 2, fid
        elif row.cdl_class == "corn":
            assert seq.count("C") >= len(YEARS) - 1, fid
        elif row.cdl_class == "pasture":
            assert seq.count("P") >= len(YEARS) - 2, fid
        else:
            assert seq.count("C") + seq.count("S") >= 5, fid


def test_primary_field_alternates_every_year(joined):
    fields, notes = joined
    (primary,) = fields.index[fields["role"] == "primary"]
    seq = notes.loc[primary, f"crops_{YEARS[0]}_{YEARS[-1]}"]
    assert set(seq) <= set("CS") and _alternations(seq) == len(YEARS) - 1
