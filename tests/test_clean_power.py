"""POWER cleaning: fill values, gaps, DS2's hard and soft checks, climate cells, and parity with DS2's reader."""

import datetime as dt
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pandera.errors
import pytest

from common.schemas import CLIMATE_DAILY, CLIMATE_POINTS
from transform.clean import power
from transform.indicators import climate as c
from transform.indicators.runner import power_frame

SAMPLE = Path(__file__).resolve().parent.parent / "data" / "sample" / "primary-001" / "power"
UNITS = {"T2M_MAX": "C", "T2M_MIN": "C", "T2M": "C", "PRECTOTCORR": "mm/day", "RH2M": "%",
         "ALLSKY_SFC_SW_DWN": "MJ/m^2/day", "WS2M": "m/s"}
SCHEMA_ERRORS = (pandera.errors.SchemaError, pandera.errors.SchemaErrors)


def document(start="20230101", end="20230110", fill=-999.0, edit=None, drop=()):
    days = pd.date_range(start, end).strftime("%Y%m%d")
    base = {"T2M_MAX": 20.0, "T2M_MIN": 5.0, "T2M": 12.0, "PRECTOTCORR": 1.5, "RH2M": 70.0,
            "ALLSKY_SFC_SW_DWN": 15.0, "WS2M": 3.0}
    parameter = {v: {d: base[v] for d in days} for v in base}
    for variable, changes in (edit or {}).items():
        for day, value in changes.items():
            if value is None:
                del parameter[variable][day]
            else:
                parameter[variable][day] = value
    for variable in drop:
        del parameter[variable]
    return {
        "geometry": {"coordinates": [-93.5, 42.0, 300.0]},
        "properties": {"parameter": parameter},
        "header": {"start": start, "end": end, "fill_value": fill},
        "parameters": {v: {"units": u} for v, u in UNITS.items()},
    }


def sample_document():
    return json.loads(next(SAMPLE.glob("*.json")).read_text())


def test_the_primary_field_sample_cleans_to_one_row_per_variable_and_day():
    result = power.clean_point(sample_document(), "primary-001")
    assert result.expected_days == 365 and len(result.daily) == 365 * 7
    assert set(result.daily["qc_flag"]) == {""} and not result.daily["value"].isna().any()
    assert result.daily.groupby("variable")["unit"].first().to_dict() == UNITS
    assert (result.latitude, result.longitude) == (42.038, -93.487)


def test_the_fill_value_becomes_null_flagged_fill_and_neighbours_are_untouched():
    doc = document(edit={"T2M": {"20230103": -999.0}})
    result = power.clean_point(doc, "p")
    row = result.daily[(result.daily.variable == "T2M") & (result.daily.date == "2023-01-03")].iloc[0]
    assert np.isnan(row["value"]) and row["qc_flag"] == "fill"
    t2m = result.daily[result.daily.variable == "T2M"].set_index("date")["value"]
    assert t2m["2023-01-02"] == 12.0 and t2m["2023-01-04"] == 12.0  # nothing interpolated
    assert result.fill_dates["T2M"] == ["2023-01-03"] and not result.fill_dates["T2M_MAX"]
    assert not (result.daily["value"] == -999.0).any()


def test_a_date_missing_from_the_response_is_a_null_row_flagged_missing_and_reported():
    result = power.clean_point(document(edit={"RH2M": {"20230105": None}}), "p")
    row = result.daily[(result.daily.variable == "RH2M") & (result.daily.date == "2023-01-05")].iloc[0]
    assert np.isnan(row["value"]) and row["qc_flag"] == "missing"
    assert result.missing_dates["RH2M"] == ["2023-01-05"] and len(result.daily) == 10 * 7


def test_a_fill_value_other_than_999_or_a_missing_variable_stops_the_run():
    with pytest.raises(ValueError, match="fill value"):
        power.clean_point(document(fill=-9999.0), "p")
    with pytest.raises(ValueError, match="variables missing"):
        power.clean_point(document(drop=("WS2M",)), "p")


def test_dates_outside_the_stated_period_are_refused():
    doc = document()
    doc["properties"]["parameter"]["T2M"]["20240101"] = 1.0
    with pytest.raises(ValueError, match="outside"):
        power.clean_point(doc, "p")


@pytest.mark.parametrize("variable, value", [
    ("PRECTOTCORR", -0.1), ("ALLSKY_SFC_SW_DWN", -1.0), ("WS2M", -0.5), ("RH2M", 100.5), ("RH2M", -1.0),
])
def test_hard_checks_stop_the_run_and_name_the_variable(variable, value):
    with pytest.raises(power.HardCheckFailed, match=variable):
        power.clean_point(document(edit={variable: {"20230102": value}}), "p")


def test_the_hard_check_boundaries_are_allowed():
    power.clean_point(document(edit={"PRECTOTCORR": {"20230102": 0.0}, "RH2M": {"20230102": 100.0}, "WS2M": {"20230102": 0.0}}), "p")


def test_a_fill_value_is_not_mistaken_for_a_negative_hard_check_failure():
    power.clean_point(document(edit={"PRECTOTCORR": {"20230102": -999.0}}), "p")  # null, not -999 mm


def test_soft_checks_flag_and_keep_the_row():
    doc = document(edit={"T2M_MIN": {"20230103": 15.0}, "T2M_MAX": {"20230104": 55.0}})
    result = power.clean_point(doc, "p")
    daily = result.daily
    order = daily[(daily.date == "2023-01-03") & daily.variable.isin(["T2M_MIN", "T2M", "T2M_MAX"])]
    assert set(order.qc_flag) == {"soft_t_order"} and 15.0 in set(order.value)  # the row is kept as it was
    hot = daily[(daily.date == "2023-01-04") & (daily.variable == "T2M_MAX")].iloc[0]
    assert hot["qc_flag"] == "soft_t_range" and hot["value"] == 55.0
    assert result.soft_flags["soft_t_order"] == 3 and result.soft_flags["soft_t_range"] == 1


def test_a_fill_flag_is_not_overwritten_by_a_soft_flag():
    doc = document(edit={"T2M": {"20230103": -999.0}, "T2M_MIN": {"20230103": 15.0}})
    daily = power.clean_point(doc, "p").daily
    assert daily[(daily.variable == "T2M") & (daily.date == "2023-01-03")].iloc[0]["qc_flag"] == "fill"


def test_points_with_identical_content_share_a_cell_and_different_content_does_not():
    a = power.clean_point(document(), "field-a")
    b = power.clean_point(document(), "field-b")
    c_ = power.clean_point(document(edit={"T2M": {"20230103": 13.0}}), "field-c")
    points, daily = power.group_cells([a, b, c_])
    cells = dict(zip(points["point_id"], points["cell_id"], strict=True))
    assert cells["field-a"] == cells["field-b"] != cells["field-c"]
    assert daily["cell_id"].nunique() == 2 and len(daily) == 2 * 10 * 7  # one copy of each cell's series
    assert (points["cell_id"].str.startswith("cell-")).all()


def test_a_fill_and_a_gap_are_different_histories_and_do_not_share_a_cell():
    filled = power.clean_point(document(edit={"T2M": {"20230103": -999.0}}), "a")
    gap = power.clean_point(document(edit={"T2M": {"20230103": None}}), "b")
    points, _ = power.group_cells([filled, gap])
    assert points["cell_id"].nunique() == 2


def test_the_cell_id_does_not_depend_on_the_point_id():
    one = power.series_fingerprint(power.clean_point(document(), "x").daily)
    two = power.series_fingerprint(power.clean_point(document(), "y").daily)
    assert one == two


def test_cleaned_frames_pass_the_pandera_schemas_and_bad_ones_do_not():
    points, daily = power.group_cells([power.clean_point(sample_document(), "primary-001")])
    CLIMATE_POINTS.validate(points)
    CLIMATE_DAILY.validate(daily)
    with pytest.raises(SCHEMA_ERRORS):
        CLIMATE_DAILY.validate(daily.assign(qc_flag="odd"))
    with pytest.raises(SCHEMA_ERRORS):
        CLIMATE_DAILY.validate(daily.assign(variable="SNOW"))
    with pytest.raises(SCHEMA_ERRORS):
        CLIMATE_DAILY.validate(pd.concat([daily, daily.head(1)], ignore_index=True))


def wide(daily: pd.DataFrame) -> pd.DataFrame:
    frame = daily.pivot(index="date", columns="variable", values="value")
    frame.index = [d.date() for d in frame.index]
    return frame


def test_parity_with_ds2s_reader_values_and_nulls_match_exactly():
    doc = document(start="20230101", end="20230131", edit={"T2M": {"20230110": -999.0}, "RH2M": {"20230111": None}})
    ours = wide(power.clean_point(doc, "p").daily)
    hers = power_frame(doc)[0].set_index("date")
    # DS2's reader turns the fill value into null but cannot see an absent date; the DE row for it is null
    assert ours.loc[dt.date(2023, 1, 10), "T2M"] != ours.loc[dt.date(2023, 1, 10), "T2M"]
    for variable in power.VARIABLES:
        a = ours[variable].drop(index=dt.date(2023, 1, 11)) if variable == "RH2M" else ours[variable]
        b = hers[variable].drop(index=dt.date(2023, 1, 11)) if variable == "RH2M" else hers[variable]
        pd.testing.assert_series_equal(a, b, check_names=False, check_dtype=False)


def test_parity_ds2s_growing_degree_days_agree_on_the_cleaned_frame():
    doc = sample_document()
    ours = wide(power.clean_point(doc, "primary-001").daily).reset_index(names=c.DATE_COLUMN)
    hers = power_frame(doc)[0]
    window = (dt.date(2023, 4, 1), dt.date(2023, 11, 30))
    assert c.growing_degree_days(ours, window).value == c.growing_degree_days(hers, window).value
