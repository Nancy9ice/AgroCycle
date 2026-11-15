"""Tests for the POWER climate indicators (roadmap Phase 4 exit check).

Run from the repository root:  python -m pytest transform/indicators -q
"""
from datetime import date, timedelta

import pandas as pd
import pytest

from transform.indicators import climate as c


def daily_frame(rows: list[tuple], columns: list[str]) -> pd.DataFrame:
    return pd.DataFrame(rows, columns=[c.DATE_COLUMN, *columns])


def constant_series(
    start: date,
    days: int,
    columns: dict[str, float],
) -> pd.DataFrame:
    dates = [start + timedelta(days=offset) for offset in range(days)]
    frame = pd.DataFrame({c.DATE_COLUMN: dates})
    for name, value in columns.items():
        frame[name] = value
    return frame


# --- growing degree days: hand-computed golden case ----------------------------------------------
GOLDEN_START = date(2003, 5, 1)
GOLDEN_WINDOW = (GOLDEN_START, date(2003, 5, 5))
GOLDEN_ROWS = [
    # clamp to [10, 30], then max(0, mean - 10):  (25+15)/2-10 = 10
    (date(2003, 5, 1), 25.0, 15.0),
    # 35 clamps to 30:                            (30+20)/2-10 = 15
    (date(2003, 5, 2), 35.0, 20.0),
    # 4 clamps up to 10:                          (12+10)/2-10 =  1
    (date(2003, 5, 3), 12.0, 4.0),
    # both clamp up to 10:                        (10+10)/2-10 =  0
    (date(2003, 5, 4), 8.0, 2.0),
    # exactly at the cap:                         (30+10)/2-10 = 10
    (date(2003, 5, 5), 30.0, 10.0),
]
GOLDEN_GDD = 36.0


def test_gdd_golden_season_matches_hand_computation():
    result = c.growing_degree_days(daily_frame(GOLDEN_ROWS, ["T2M_MAX", "T2M_MIN"]), GOLDEN_WINDOW)
    assert result.value == pytest.approx(GOLDEN_GDD)
    assert result.unit == "degree-days C"
    assert (result.days_expected, result.days_valid) == (5, 5)
    assert result.status == "ok"
    assert result.reason is None


def test_gdd_cold_day_contributes_zero_not_a_negative():
    rows = [(date(2003, 5, 1), 5.0, -10.0)]
    result = c.growing_degree_days(daily_frame(rows, ["T2M_MAX", "T2M_MIN"]), (GOLDEN_START, GOLDEN_START))
    assert result.value == pytest.approx(0.0)


def test_gdd_respects_a_different_base_and_cap():
    result = c.growing_degree_days(
        daily_frame(GOLDEN_ROWS, ["T2M_MAX", "T2M_MIN"]),
        GOLDEN_WINDOW,
        base_c=0.0,
        upper_cap_c=40.0,
    )
    # (20 + 27.5 + 8 + 5 + 20) with no clamping at either end
    assert result.value == pytest.approx(80.5)


def test_gdd_rejects_a_cap_at_or_below_the_base():
    with pytest.raises(ValueError, match="must exceed"):
        c.growing_degree_days(
            daily_frame(GOLDEN_ROWS, ["T2M_MAX", "T2M_MIN"]), GOLDEN_WINDOW, base_c=10.0, upper_cap_c=10.0
        )


def test_gdd_is_unknown_when_coverage_is_short():
    result = c.growing_degree_days(
        daily_frame(GOLDEN_ROWS[:2], ["T2M_MAX", "T2M_MIN"]), (GOLDEN_START, date(2003, 5, 10))
    )
    assert result.value is None
    assert result.status == "unknown"
    assert (result.days_expected, result.days_valid) == (10, 2)
    assert "coverage" in result.reason


def test_gdd_reports_the_denominator_when_a_day_is_null():
    rows = list(GOLDEN_ROWS)
    rows[2] = (date(2003, 5, 3), None, 4.0)
    result = c.growing_degree_days(
        daily_frame(rows, ["T2M_MAX", "T2M_MIN"]), GOLDEN_WINDOW, min_coverage=0.5
    )
    assert result.value == pytest.approx(GOLDEN_GDD - 1.0)
    assert (result.days_expected, result.days_valid) == (5, 4)


# --- a null day is not a zero -------------------------------------------------------------------
def test_mean_temperature_does_not_pull_a_null_day_towards_zero():
    frame = constant_series(date(2020, 6, 1), 10, {"T2M": 20.0})
    frame.loc[frame[c.DATE_COLUMN] == date(2020, 6, 5), "T2M"] = None
    result = c.seasonal_mean_temperature(frame, (date(2020, 6, 1), date(2020, 6, 10)), min_coverage=0.5)
    assert result.value == pytest.approx(20.0)
    assert (result.days_expected, result.days_valid) == (10, 9)


def test_null_day_breaks_a_dry_spell_instead_of_extending_it():
    frame = constant_series(date(2020, 6, 1), 10, {"PRECTOTCORR": 0.0})
    frame.loc[frame[c.DATE_COLUMN] == date(2020, 6, 6), "PRECTOTCORR"] = None
    result = c.longest_dry_spell(frame, (date(2020, 6, 1), date(2020, 6, 10)), min_coverage=0.5)
    assert result.value == pytest.approx(5.0)
    assert (result.days_expected, result.days_valid) == (10, 9)


def test_absent_date_breaks_a_dry_spell():
    frame = constant_series(date(2020, 6, 1), 10, {"PRECTOTCORR": 0.0})
    frame = frame[frame[c.DATE_COLUMN] != date(2020, 6, 4)]
    result = c.longest_dry_spell(frame, (date(2020, 6, 1), date(2020, 6, 10)), min_coverage=0.5)
    assert result.value == pytest.approx(6.0)
    assert (result.days_expected, result.days_valid) == (10, 9)


# --- heat days ----------------------------------------------------------------------------------
def test_heat_days_threshold_is_inclusive():
    rows = [
        (date(2020, 7, 1), 29.9),
        (date(2020, 7, 2), 30.0),
        (date(2020, 7, 3), 40.0),
    ]
    result = c.heat_days(daily_frame(rows, ["T2M_MAX"]), (date(2020, 7, 1), date(2020, 7, 3)))
    assert result.value == pytest.approx(2.0)
    assert result.unit == "days"


def test_heat_days_counts_only_days_with_data():
    rows = [
        (date(2020, 7, 1), 35.0),
        (date(2020, 7, 2), None),
        (date(2020, 7, 3), 35.0),
    ]
    result = c.heat_days(
        daily_frame(rows, ["T2M_MAX"]), (date(2020, 7, 1), date(2020, 7, 3)), min_coverage=0.5
    )
    assert result.value == pytest.approx(2.0)
    assert (result.days_expected, result.days_valid) == (3, 2)


# --- precipitation ------------------------------------------------------------------------------
def test_precipitation_total_sums_the_window():
    rows = [
        (date(2020, 6, 1), 10.0),
        (date(2020, 6, 2), 0.0),
        (date(2020, 6, 3), 2.5),
    ]
    result = c.seasonal_precipitation_total(
        daily_frame(rows, ["PRECTOTCORR"]), (date(2020, 6, 1), date(2020, 6, 3))
    )
    assert result.value == pytest.approx(12.5)
    assert result.unit == "mm"


def test_longest_dry_spell_finds_the_longest_run():
    rows = [
        (date(2020, 6, 1), 0.0),
        (date(2020, 6, 2), 0.5),
        (date(2020, 6, 3), 5.0),
        (date(2020, 6, 4), 0.0),
        (date(2020, 6, 5), 0.0),
        (date(2020, 6, 6), 0.9),
        (date(2020, 6, 7), 3.0),
    ]
    result = c.longest_dry_spell(
        daily_frame(rows, ["PRECTOTCORR"]), (date(2020, 6, 1), date(2020, 6, 7))
    )
    assert result.value == pytest.approx(3.0)


def test_dry_spell_count_applies_the_minimum_length():
    frame = constant_series(date(2020, 6, 1), 30, {"PRECTOTCORR": 0.0})
    for wet in (date(2020, 6, 13), date(2020, 6, 14)):
        frame.loc[frame[c.DATE_COLUMN] == wet, "PRECTOTCORR"] = 20.0
    window = (date(2020, 6, 1), date(2020, 6, 30))
    assert c.dry_spell_count(frame, window, min_days=10).value == pytest.approx(2.0)
    assert c.dry_spell_count(frame, window, min_days=17).value == pytest.approx(0.0)
    assert c.longest_dry_spell(frame, window).value == pytest.approx(16.0)


def test_dry_spell_count_rejects_a_zero_minimum():
    frame = constant_series(date(2020, 6, 1), 3, {"PRECTOTCORR": 0.0})
    with pytest.raises(ValueError, match="at least 1"):
        c.dry_spell_count(frame, (date(2020, 6, 1), date(2020, 6, 3)), min_days=0)


# --- frost --------------------------------------------------------------------------------------
def frost_year(year: int = 2020) -> pd.DataFrame:
    start = date(year, 1, 1)
    days = (date(year, 12, 31) - start).days + 1
    dates = [start + timedelta(days=offset) for offset in range(days)]
    frost_free = [date(year, 5, 1) <= day <= date(year, 9, 30) for day in dates]
    return pd.DataFrame(
        {
            c.DATE_COLUMN: dates,
            "T2M_MIN": [10.0 if warm else -5.0 for warm in frost_free],
        }
    )


def test_frost_window_finds_both_dates_and_the_span():
    result = c.frost_window(frost_year(), (date(2020, 1, 1), date(2020, 12, 31)))
    assert result.status == "ok"
    assert result.last_spring_frost == date(2020, 4, 30)
    assert result.first_autumn_frost == date(2020, 10, 1)
    assert result.frost_free_days == 153
    assert result.frost_free_days == (result.first_autumn_frost - result.last_spring_frost).days - 1


def test_frost_window_is_unknown_without_a_frost_on_both_sides():
    frame = constant_series(date(2020, 1, 1), 366, {"T2M_MIN": 12.0})
    result = c.frost_window(frame, (date(2020, 1, 1), date(2020, 12, 31)))
    assert result.status == "unknown"
    assert result.frost_free_days is None
    assert result.last_spring_frost is None
    assert "both sides" in result.reason


def test_frost_window_accepts_an_explicit_split():
    result = c.frost_window(
        frost_year(), (date(2020, 1, 1), date(2020, 12, 31)), split=date(2020, 3, 1)
    )
    # With the split in March, the first frost after it is 2 March, not October.
    assert result.last_spring_frost == date(2020, 3, 1)
    assert result.first_autumn_frost == date(2020, 3, 2)
    assert result.frost_free_days == 0


def test_frost_window_is_unknown_when_coverage_is_short():
    frame = frost_year().iloc[:100]
    result = c.frost_window(frame, (date(2020, 1, 1), date(2020, 12, 31)))
    assert result.status == "unknown"
    assert "coverage" in result.reason


# --- input contract ------------------------------------------------------------------------------
def test_duplicate_date_is_rejected():
    rows = [(date(2020, 6, 1), 1.0), (date(2020, 6, 1), 2.0)]
    with pytest.raises(ValueError, match="duplicate date"):
        c.seasonal_precipitation_total(
            daily_frame(rows, ["PRECTOTCORR"]), (date(2020, 6, 1), date(2020, 6, 1))
        )


def test_missing_variable_column_is_rejected():
    frame = constant_series(date(2020, 6, 1), 3, {"T2M": 20.0})
    with pytest.raises(KeyError, match="T2M_MAX"):
        c.growing_degree_days(frame, (date(2020, 6, 1), date(2020, 6, 3)))


def test_missing_date_column_is_rejected():
    frame = pd.DataFrame({"T2M_MAX": [20.0], "T2M_MIN": [10.0]})
    with pytest.raises(KeyError, match=c.DATE_COLUMN):
        c.growing_degree_days(frame, (date(2020, 6, 1), date(2020, 6, 1)))


def test_window_end_before_start_is_rejected():
    with pytest.raises(ValueError, match="precedes start"):
        c.expected_days((date(2020, 6, 10), date(2020, 6, 1)))


# --- reference ET -------------------------------------------------------------------------------
IOWA_LATITUDE = 42.0167
IOWA_ELEVATION_M = 335.0
SUMMER_DAY = {
    "t_max_c": 30.0,
    "t_min_c": 18.0,
    "t_mean_c": 24.0,
    "rh_pct": 70.0,
    "radiation_mj": 25.0,
    "wind_ms": 3.0,
    "latitude_deg": IOWA_LATITUDE,
    "elevation_m": IOWA_ELEVATION_M,
    "day_of_year": 196,
}


def test_et0_summer_day_is_physically_plausible():
    value = c.et0_fao56_daily(**SUMMER_DAY)
    # A humid mid-July day in central Iowa: single-figure mm/day, not tens.
    assert 3.0 < value < 8.0


def test_et0_pins_the_current_implementation():
    # A change detector, not an independent check: see the ET0 limitation in INDICATOR_LINEAGE.
    assert c.et0_fao56_daily(**SUMMER_DAY) == pytest.approx(5.447642, abs=1e-6)


def test_et0_rises_with_radiation_wind_and_dryness():
    base = c.et0_fao56_daily(**SUMMER_DAY)
    assert c.et0_fao56_daily(**{**SUMMER_DAY, "radiation_mj": 30.0}) > base
    assert c.et0_fao56_daily(**{**SUMMER_DAY, "wind_ms": 6.0}) > base
    assert c.et0_fao56_daily(**{**SUMMER_DAY, "rh_pct": 40.0}) > base


def test_et0_is_never_negative_in_midwinter():
    value = c.et0_fao56_daily(
        t_max_c=-2.0,
        t_min_c=-10.0,
        t_mean_c=-6.0,
        rh_pct=80.0,
        radiation_mj=5.0,
        wind_ms=2.0,
        latitude_deg=IOWA_LATITUDE,
        elevation_m=IOWA_ELEVATION_M,
        day_of_year=15,
    )
    assert value >= 0.0


def test_extraterrestrial_radiation_follows_the_season():
    midsummer = c._extraterrestrial_radiation(IOWA_LATITUDE, 172)
    midwinter = c._extraterrestrial_radiation(IOWA_LATITUDE, 355)
    assert midsummer > midwinter
    assert c._extraterrestrial_radiation(IOWA_LATITUDE, 150) == pytest.approx(
        c._extraterrestrial_radiation(IOWA_LATITUDE, 194), abs=0.5
    )
    assert c._extraterrestrial_radiation(-IOWA_LATITUDE, 172) < midsummer


def test_reference_et_total_sums_daily_values():
    frame = constant_series(
        date(2020, 7, 1),
        5,
        {
            "T2M_MAX": 30.0,
            "T2M_MIN": 18.0,
            "T2M": 24.0,
            "RH2M": 70.0,
            "ALLSKY_SFC_SW_DWN": 25.0,
            "WS2M": 3.0,
        },
    )
    window = (date(2020, 7, 1), date(2020, 7, 5))
    result = c.reference_et_total(frame, window, IOWA_LATITUDE, IOWA_ELEVATION_M)
    assert result.status == "ok"
    assert result.value == pytest.approx(5 * 5.44, abs=0.2)
    assert result.days_valid == 5


def test_reference_et_is_unknown_when_one_input_is_missing():
    frame = constant_series(
        date(2020, 7, 1),
        5,
        {
            "T2M_MAX": 30.0,
            "T2M_MIN": 18.0,
            "T2M": 24.0,
            "RH2M": 70.0,
            "ALLSKY_SFC_SW_DWN": 25.0,
            "WS2M": 3.0,
        },
    )
    frame.loc[frame[c.DATE_COLUMN] >= date(2020, 7, 3), "WS2M"] = None
    result = c.reference_et_total(
        frame, (date(2020, 7, 1), date(2020, 7, 5)), IOWA_LATITUDE, IOWA_ELEVATION_M
    )
    assert result.value is None
    assert result.status == "unknown"
    assert result.days_valid == 2


# --- lineage ------------------------------------------------------------------------------------
def test_every_indicator_has_a_complete_lineage_row():
    assert len(c.INDICATOR_LINEAGE) == 10
    for row in c.INDICATOR_LINEAGE:
        missing = [field for field in c.LINEAGE_FIELDS if not row.get(field)]
        assert not missing, f"{row.get('indicator_id')} is missing {missing}"
        assert row["evidence_type"] == "model_reanalysis"
        assert "not a field" in row["spatial_scale"]


def test_lineage_ids_are_unique_and_cover_every_indicator():
    ids = [row["indicator_id"] for row in c.INDICATOR_LINEAGE]
    assert len(ids) == len(set(ids))
    assert set(ids) == {
        "gdd",
        "heat_days",
        "precipitation_total",
        "mean_temperature",
        "longest_dry_spell",
        "dry_spell_count",
        "frost_window",
        "frost_free_days",
        "reference_et_total",
        "gdd_season_difference_vs_marsden",
    }


def test_unreviewed_thresholds_are_declared_in_the_lineage():
    for indicator_id in ("gdd", "heat_days", "longest_dry_spell", "dry_spell_count", "frost_window"):
        row = next(r for r in c.INDICATOR_LINEAGE if r["indicator_id"] == indicator_id)
        assert "not expert-reviewed" in row["limitation"]


def test_reference_et_declares_that_it_is_not_validated():
    row = next(r for r in c.INDICATOR_LINEAGE if r["indicator_id"] == "reference_et_total")
    assert "not independently validated" in row["limitation"]
