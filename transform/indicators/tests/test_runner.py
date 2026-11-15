"""Tests for the indicator runner (roadmap Phase 4).

The invariant that matters to the load: every indicator written to either table has exactly one lineage
record, and no lineage row points at an indicator nothing wrote. The load refuses an indicator without a
record, so this is checked here rather than discovered at load time.

Run from the repository root:  uv run pytest transform/indicators -q
"""
import datetime as dt

import pandas as pd
import pytest

from transform.indicators import climate as c
from transform.indicators import runner as r
from transform.indicators import soil as s

# Everything the runner can write, in the ids it writes them under.
CLIMATE_IDS = {
    "gdd",
    "heat_days",
    "precipitation_total",
    "mean_temperature",
    "longest_dry_spell",
    "dry_spell_count",
    "reference_et_total",
    "frost_free_days",
    "gdd_season_difference_vs_marsden",
}
SOIL_INDICATOR_IDS = {
    "om_r_0_30cm",
    "claytotal_r_0_30cm",
    "sandtotal_r_0_30cm",
    "silttotal_r_0_30cm",
    "ph1to1h2o_r_0_30cm",
    "available_water_storage_0_100cm",
    "slope_r",
    "drainagecl_dominant",
    "hydgrp_dominant",
}
COMPOSITION_IDS = {"map_unit_share", "drainagecl", "hydgrp"}
ALL_EMITTED = CLIMATE_IDS | SOIL_INDICATOR_IDS | COMPOSITION_IDS


def test_every_emitted_indicator_has_a_lineage_record():
    rows = r.lineage_rows("test-run", ALL_EMITTED)
    assert {row["indicator_id"] for row in rows} == ALL_EMITTED


def test_a_missing_lineage_record_raises_before_anything_is_written():
    with pytest.raises(RuntimeError, match="no lineage record for indicator"):
        r.lineage_rows("test-run", ALL_EMITTED | {"invented_indicator"})


def test_lineage_is_not_written_for_indicators_this_run_did_not_emit():
    rows = r.lineage_rows("test-run", {"gdd"})
    assert [row["indicator_id"] for row in rows] == ["gdd"]


def test_every_lineage_row_is_complete_and_labelled():
    for row in r.lineage_rows("test-run", ALL_EMITTED):
        for field in ("formula", "aggregation_window", "spatial_support", "limitation", "resolution"):
            assert row[field], f"{row['indicator_id']} has an empty {field}"
        assert row["evidence_type"] in ("model_reanalysis", "survey")
        assert row["scale"] in ("grid", "field")
        assert row["code_version"] == r.CODE_VERSION


def test_climate_and_soil_lineage_ids_are_unique_across_both_modules():
    ids = [record["indicator_id"] for record in c.INDICATOR_LINEAGE + s.SOIL_PROPERTY_LINEAGE]
    assert len(ids) == len(set(ids))


# --- the shaping functions, without touching S3 ---------------------------------------------------
def test_power_frame_masks_the_fill_value():
    document = {
        "header": {"fill_value": -999.0},
        "geometry": {"coordinates": [-93.8, 42.0, 310.0]},
        "properties": {
            "parameter": {
                "T2M": {"20230101": 1.0, "20230102": -999.0},
                "T2M_MAX": {"20230101": 3.0, "20230102": 4.0},
            }
        },
    }
    frame, latitude, longitude, elevation = r.power_frame(document)
    assert (latitude, longitude, elevation) == (42.0, -93.8, 310.0)
    assert frame[c.DATE_COLUMN].tolist() == [dt.date(2023, 1, 1), dt.date(2023, 1, 2)]
    assert pd.isna(frame.loc[1, "T2M"])
    assert frame.loc[1, "T2M_MAX"] == 4.0


def test_seasons_cover_april_to_november():
    windows = r.seasons(2015, 2016)
    assert windows == [
        (dt.date(2015, 4, 1), dt.date(2015, 11, 30)),
        (dt.date(2016, 4, 1), dt.date(2016, 11, 30)),
    ]
    assert c.expected_days(windows[0]) == 244


def test_soil_tables_compute_shares_that_sum_to_one():
    square = "POLYGON((-93.80 42.00, -93.79 42.00, -93.79 42.01, -93.80 42.01, -93.80 42.00))"
    half = "POLYGON((-93.80 42.00, -93.795 42.00, -93.795 42.01, -93.80 42.01, -93.80 42.00))"
    step_a = [["mukey", "isect_wkt"], ["MU1", square], ["MU2", half]]
    step_b = [["mukey", "cokey", "comppct_r", "muname"], ["MU1", "C1", "100", "Clarion"]]
    step_c = [["cokey", "chkey", "hzdept_r", "hzdepb_r", "om_r"], ["C1", "H1", "0", "30", "4.0"]]

    map_units, components, horizons = r.soil_tables("F1", step_a, step_b, step_c)
    assert map_units["area_share"].sum() == pytest.approx(1.0)
    # The full square is twice the half, so the shares must be 2:1.
    assert map_units.set_index("mukey").loc["MU1", "area_share"] == pytest.approx(2 / 3, abs=1e-3)
    assert components["comppct_r"].tolist() == [100.0]
    assert horizons["hzdepb_r"].tolist() == [30.0]


def test_climate_distance_is_null_rather_than_zero_without_a_reference():
    windows = r.seasons(2015, 2015)
    row = r.climate_distance_row("F1", [], None, windows, "test-run")
    assert row["value"] is None
    assert row["status"] == "unknown"
    assert "no Marsden-site reference" in row["unknown_reason"]


def test_climate_distance_uses_the_absolute_difference():
    windows = r.seasons(2015, 2016)
    field_rows = [
        {"indicator_id": "gdd", "value": 1900.0},
        {"indicator_id": "gdd", "value": 2000.0},
    ]
    row = r.climate_distance_row("F1", field_rows, 2000.0, windows, "test-run")
    assert row["value"] == pytest.approx(50.0)
    assert row["status"] == "available"
