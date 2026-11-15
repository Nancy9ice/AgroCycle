"""The cleaning against the real Phase 1 pulls. Skips when the raw files are not on this machine (DE only)."""

import pandas as pd
import pytest

from transform.clean import power, ssurgo
from transform.clean.sources import (
    MARSDEN_POINT,
    SSURGO_STEPS,
    Raw,
    default_power_dir,
    default_ssurgo_dir,
)
from transform.field_schema import load_fields
from transform.indicators import climate as c
from transform.indicators.runner import power_frame

HAVE_POWER = (default_power_dir() / "primary-001_19910101-20251231.json").exists()
HAVE_SSURGO = (default_ssurgo_dir() / "primary-001" / "step_a_map_units.json").exists()


@pytest.fixture(scope="module")
def points():
    raw = Raw()
    ids = [*load_fields()["field_id"], MARSDEN_POINT]
    return {p: (raw.power(p), power.clean_point(raw.power(p), p)) for p in ids}


@pytest.mark.skipif(not HAVE_POWER, reason="the POWER pull is not on this machine")
def test_every_point_has_every_day_of_every_variable_and_the_known_four_fill_values(points):
    assert len(points) == 46
    for point_id, (_, result) in points.items():
        assert result.expected_days == 12_784 and len(result.daily) == 12_784 * 7, point_id
        assert not any(result.missing_dates.values()), point_id
    fills = {(p, v, d) for p, (_, r) in points.items() for v, dates in r.fill_dates.items() for d in dates}
    assert len(fills) == 4 and {v for _, v, _ in fills} == {"ALLSKY_SFC_SW_DWN"}
    assert {d for _, _, d in fills} == {"1991-11-29"}  # the four fill values found in Phase 1


@pytest.mark.skipif(not HAVE_POWER, reason="the POWER pull is not on this machine")
def test_the_46_points_fall_into_the_7_distinct_series_sets_found_in_phase_1(points):
    table, daily = power.group_cells([r for _, r in points.values()])
    assert table["cell_id"].nunique() == 7 and set(table["point_id"]) == set(points)
    assert len(daily) == 7 * 7 * 12_784


@pytest.mark.skipif(not HAVE_POWER, reason="the POWER pull is not on this machine")
def test_cleaned_values_equal_ds2s_reader_for_every_point(points):
    for point_id, (document, result) in points.items():
        ours = result.daily.pivot(index="date", columns="variable", values="value")
        hers = power_frame(document)[0].set_index("date")
        hers.index = pd.to_datetime(hers.index)
        for variable in power.VARIABLES:
            assert ours[variable].equals(hers[variable].astype("float64").rename_axis("date")), (point_id, variable)


@pytest.mark.skipif(not HAVE_POWER, reason="the POWER pull is not on this machine")
def test_ds2s_gdd_season_is_the_same_on_the_cleaned_frame(points):
    import datetime as dt

    document, result = points["primary-001"]
    cleaned = result.daily.pivot(index="date", columns="variable", values="value")
    cleaned.index = [d.date() for d in cleaned.index]
    cleaned = cleaned.reset_index(names=c.DATE_COLUMN)
    for year in (2015, 2020, 2025):
        window = (dt.date(year, 4, 1), dt.date(year, 11, 30))
        assert c.growing_degree_days(cleaned, window).value == c.growing_degree_days(power_frame(document)[0], window).value


@pytest.mark.skipif(not HAVE_SSURGO, reason="the SSURGO pull is not on this machine")
def test_all_45_fields_clean_with_no_findings_and_ds2s_check_agrees():
    from transform.indicators import soil as s

    raw, results = Raw(), []
    for field_id in load_fields()["field_id"]:
        results.append(ssurgo.clean_field(field_id, *(raw.ssurgo(field_id, step) for step in SSURGO_STEPS)))
    assert [f for r in results for f in r.findings] == []
    assert (sum(len(r.map_units) for r in results), sum(len(r.components) for r in results),
            sum(len(r.horizons) for r in results)) == (274, 872, 3422)
    assert all(s.check_soil_tables(r.map_units, r.components, r.horizons) == [] for r in results)
