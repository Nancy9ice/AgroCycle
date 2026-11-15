import io
import json

import pandera.pandas as pa
import pytest

from common import schema_check
from transform.nass import clean


def _row(value="190.1", county="STORY", commodity="CORN", statistic="YIELD", unit="BU / ACRE",
         year=2020, util="GRAIN", cls="ALL CLASSES", cv="2.4"):
    return {"Value": value, "county_name": county, "state_fips_code": "19",
            "county_code": "169" if county == "STORY" else "015", "year": str(year),
            "commodity_desc": commodity, "class_desc": cls, "util_practice_desc": util,
            "statisticcat_desc": statistic, "unit_desc": unit, "CV (%)": cv,
            "short_desc": f"{commodity} - {statistic}", "source_desc": "SURVEY", "agg_level_desc": "COUNTY",
            "state_alpha": "IA", "domain_desc": "TOTAL", "prodn_practice_desc": "ALL PRODUCTION PRACTICES",
            "freq_desc": "ANNUAL", "reference_period_desc": "YEAR"}


def _body(*rows):
    return json.dumps({"data": list(rows)}).encode()


def test_values_parse_with_commas_and_withheld_become_null():
    assert clean.parse_value("1,234.5") == (1234.5, "reported")
    assert clean.parse_value("                 (D)") == (None, "withheld")
    assert clean.parse_cv("") is None and clean.parse_cv("2.4") == 2.4


@pytest.mark.parametrize("code", ["(Z)", "(NA)", "(S)", ""])
def test_codes_other_than_d_stop_the_run_instead_of_being_called_withheld(code):
    """(Z) means less than half the unit shown, (NA) not available: neither is "withheld"."""
    with pytest.raises(ValueError, match="unhandled NASS value"):
        clean.parse_value(code)


@pytest.mark.parametrize("field, value", [
    ("domain_desc", "IRRIGATED"), ("prodn_practice_desc", "IRRIGATED"), ("freq_desc", "MONTHLY"),
    ("reference_period_desc", "MARKETING YEAR"),
])
def test_a_row_from_another_series_stops_the_run(field, value):
    with pytest.raises(ValueError, match="unexpected NASS series"):
        clean.build([_body({**_row(), field: value})])


def test_county_and_fips_must_agree():
    wrong = {**_row(), "county_code": "015"}  # Story with Boone's code
    with pytest.raises(pa.errors.SchemaError, match="county and county_fips"):
        clean.build([_body(wrong)])


class _FakeS3:
    """Objects as {key: bytes}; enough of the client for clean.read_s3."""

    def __init__(self, objects):
        self.objects = objects

    def list_objects_v2(self, Bucket, Prefix, **_):
        return {"Contents": [{"Key": k, "Size": len(v)} for k, v in self.objects.items() if k.startswith(Prefix)]}

    def get_object(self, Bucket, Key):
        return {"Body": io.BytesIO(self.objects[Key])}


def test_read_s3_takes_every_date_and_the_newest_copy_of_each_file():
    """A pull resumed on a later day: the county pulled earlier must not be dropped."""
    prefix = "raw/nass/api_GET/"
    s3 = _FakeS3({
        f"{prefix}2026-11-14/story_corn_yield_2003-2025.json": b"old story",
        f"{prefix}2026-11-14/boone_corn_yield_2003-2025.json": b"old boone",
        f"{prefix}2026-11-15/boone_corn_yield_2003-2025.json": b"new boone",
        f"{prefix}2026-11-15/boone_corn_yield_2003-2025.json.manifest.json": b"{}",
    })
    assert clean.read_s3(s3, "bucket") == [b"new boone", b"old story"]


def test_build_keeps_withheld_as_null_and_never_fills_them():
    frame = clean.build([_body(_row(), _row(value="   (D)", year=2021, cv=""))])
    withheld = frame[frame["value_status"] == "withheld"]
    assert len(frame) == 2 and len(withheld) == 1 and withheld["value"].isna().all()
    assert set(frame["county_fips"]) == {"19169"} and set(frame["county"]) == {"Story"}


def test_corn_grain_and_silage_stay_separate_rows():
    frame = clean.build([_body(_row(), _row(util="SILAGE", unit="TONS / ACRE", value="20"))])
    assert len(frame) == 2 and set(frame["unit"]) == {"BU / ACRE", "TONS / ACRE"}


@pytest.mark.parametrize("row, text", [
    (_row(value="900"), "yield above"),
    (_row(statistic="AREA PLANTED", unit="BU"), "unit does not belong"),
    (_row(year=1990), "year"),
    (_row(value="-5"), "value"),
    (_row(commodity="HAY", statistic="AREA PLANTED", unit="ACRES", util="ALL UTILIZATION PRACTICES"),
     "no planted area for hay"),
])
def test_bad_rows_fail_the_schema(row, text):
    with pytest.raises(pa.errors.SchemaError) as err:
        clean.build([_body(row)])
    assert text in str(err.value)


def test_duplicate_keys_fail():
    with pytest.raises(Exception, match="duplicated|unique"):
        clean.build([_body(_row(), _row())])


def test_the_sql_names_the_schema_columns():
    assert schema_check.problems() == []
