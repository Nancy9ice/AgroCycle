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
            "short_desc": f"{commodity} - {statistic}"}


def _body(*rows):
    return json.dumps({"data": list(rows)}).encode()


def test_values_parse_with_commas_and_withheld_become_null():
    assert clean.parse_value("1,234.5") == (1234.5, "reported")
    assert clean.parse_value("                 (D)") == (None, "withheld")
    assert clean.parse_value("(Z)") == (None, "withheld")
    assert clean.parse_cv("") is None and clean.parse_cv("2.4") == 2.4


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
