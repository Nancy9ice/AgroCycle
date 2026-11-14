"""Tests for the SSURGO field aggregation (roadmap Phase 4, DS2 half).

Run from the repository root:  python -m pytest transform/indicators -q
"""
import pandas as pd
import pytest

from transform.indicators import soil as s


def map_units(rows: list[tuple]) -> pd.DataFrame:
    return pd.DataFrame(rows, columns=["field_id", "mukey", "area_share"])


def components(rows: list[tuple], columns: list[str]) -> pd.DataFrame:
    return pd.DataFrame(rows, columns=["mukey", "cokey", "comppct_r", *columns])


def horizons(rows: list[tuple], columns: list[str]) -> pd.DataFrame:
    return pd.DataFrame(rows, columns=["cokey", "chkey", "hzdept_r", "hzdepb_r", *columns])


# --- hand-computed weighting chain ---------------------------------------------------------------
# MU1 is 60% of the field: C1 at 70% has 25 cm of om 4.0 then 5 cm of om 2.0 inside 0-30 cm, so
#   (25*4 + 5*2) / 30 = 3.666667; C2 at 30% has 30 cm of om 3.0.
#   MU1 = (70*3.666667 + 30*3.0) / 100 = 3.466667
# MU2 is 40% of the field: C3 at 100% has 30 cm of om 1.0, so MU2 = 1.0
# Field  = 0.6*3.466667 + 0.4*1.0 = 2.48
GOLDEN_MAP_UNITS = map_units([("F1", "MU1", 0.6), ("F1", "MU2", 0.4)])
GOLDEN_COMPONENTS = components(
    [
        ("MU1", "C1", 70.0),
        ("MU1", "C2", 30.0),
        ("MU2", "C3", 100.0),
    ],
    [],
)
GOLDEN_HORIZONS = horizons(
    [
        ("C1", "H1", 0.0, 25.0, 4.0),
        ("C1", "H2", 25.0, 60.0, 2.0),
        ("C2", "H3", 0.0, 30.0, 3.0),
        ("C3", "H4", 0.0, 30.0, 1.0),
    ],
    ["om_r"],
)
GOLDEN_OM = 2.48


def test_golden_weighting_chain_matches_hand_computation():
    result = s.aggregate_horizon_property(
        GOLDEN_MAP_UNITS, GOLDEN_COMPONENTS, GOLDEN_HORIZONS, "F1", "om_r"
    )
    assert result.value == pytest.approx(GOLDEN_OM)
    assert result.property_id == "om_r_0_30cm"
    assert result.unit == "% by weight"
    assert (result.depth_top_cm, result.depth_bottom_cm) == (0.0, 30.0)
    assert result.area_coverage == pytest.approx(1.0)
    assert result.depth_coverage == pytest.approx(1.0)
    assert result.map_units == 2
    assert result.status == "ok"
    assert result.reason is None


def test_horizon_is_clipped_to_the_requested_interval():
    value, thickness = s.component_depth_weighted_value(GOLDEN_HORIZONS, "C1", "om_r", 0.0, 30.0)
    assert value == pytest.approx(110.0 / 30.0)
    assert thickness == pytest.approx(30.0)

    deeper, deep_thickness = s.component_depth_weighted_value(GOLDEN_HORIZONS, "C1", "om_r", 30.0, 60.0)
    assert deeper == pytest.approx(2.0)
    assert deep_thickness == pytest.approx(30.0)


def test_component_below_the_interval_contributes_nothing():
    value, thickness = s.component_depth_weighted_value(GOLDEN_HORIZONS, "C3", "om_r", 50.0, 100.0)
    assert value is None
    assert thickness == pytest.approx(0.0)


def test_depth_interval_must_be_positive():
    with pytest.raises(ValueError, match="must exceed"):
        s.component_depth_weighted_value(GOLDEN_HORIZONS, "C1", "om_r", 30.0, 30.0)


# --- nothing is filled ---------------------------------------------------------------------------
def test_null_horizon_property_lowers_coverage_rather_than_becoming_zero():
    frame = horizons(
        [
            ("C1", "H1", 0.0, 25.0, 4.0),
            ("C1", "H2", 25.0, 30.0, None),
        ],
        ["om_r"],
    )
    value, thickness = s.component_depth_weighted_value(frame, "C1", "om_r", 0.0, 30.0)
    assert value == pytest.approx(4.0)
    assert thickness == pytest.approx(25.0)


def test_component_without_horizons_counts_against_depth_coverage():
    # 20% of the map unit is water: it has a comppct_r and no horizon data.
    units = map_units([("F1", "MU1", 1.0)])
    parts = components([("MU1", "C1", 80.0), ("MU1", "WATER", 20.0)], [])
    layers = horizons([("C1", "H1", 0.0, 30.0, 3.0)], ["om_r"])

    result = s.aggregate_horizon_property(units, parts, layers, "F1", "om_r")
    assert result.value == pytest.approx(3.0)
    assert result.depth_coverage == pytest.approx(0.8)
    assert result.area_coverage == pytest.approx(1.0)


def test_a_null_area_share_makes_the_field_unknown():
    units = map_units([("F1", "MU1", 0.6), ("F1", "MU2", None)])
    result = s.aggregate_horizon_property(units, GOLDEN_COMPONENTS, GOLDEN_HORIZONS, "F1", "om_r")
    assert result.value is None
    assert result.status == "unknown"
    assert "equal weights are not assumed" in result.reason


def test_area_coverage_below_the_threshold_is_unknown_but_reported():
    layers = horizons([("C1", "H1", 0.0, 30.0, 4.0), ("C2", "H3", 0.0, 30.0, 3.0)], ["om_r"])
    result = s.aggregate_horizon_property(
        GOLDEN_MAP_UNITS, GOLDEN_COMPONENTS, layers, "F1", "om_r"
    )
    assert result.value is None
    assert result.status == "unknown"
    assert result.area_coverage == pytest.approx(0.6)
    assert "60%" in result.reason


def test_a_lower_threshold_accepts_partial_coverage():
    layers = horizons([("C1", "H1", 0.0, 30.0, 4.0), ("C2", "H3", 0.0, 30.0, 3.0)], ["om_r"])
    result = s.aggregate_horizon_property(
        GOLDEN_MAP_UNITS, GOLDEN_COMPONENTS, layers, "F1", "om_r", min_area_coverage=0.5
    )
    # MU1 alone: (70*4.0 + 30*3.0) / 100 = 3.7
    assert result.value == pytest.approx(3.7)
    assert result.area_coverage == pytest.approx(0.6)
    assert result.status == "ok"


def test_property_absent_everywhere_is_unknown():
    layers = horizons([("C1", "H1", 0.0, 30.0, None)], ["om_r"])
    result = s.aggregate_horizon_property(
        GOLDEN_MAP_UNITS, GOLDEN_COMPONENTS, layers, "F1", "om_r"
    )
    assert result.value is None
    assert "no component in any map unit reports om_r" in result.reason


def test_a_field_with_no_map_units_is_a_geometry_problem():
    with pytest.raises(ValueError, match="geometry problem"):
        s.aggregate_horizon_property(
            GOLDEN_MAP_UNITS, GOLDEN_COMPONENTS, GOLDEN_HORIZONS, "F9", "om_r"
        )


# --- available water storage ---------------------------------------------------------------------
def test_available_water_storage_sums_thickness_times_awc():
    units = map_units([("F1", "MU1", 1.0)])
    parts = components([("MU1", "C1", 100.0)], [])
    layers = horizons(
        [
            ("C1", "H1", 0.0, 50.0, 0.20),
            ("C1", "H2", 50.0, 120.0, 0.10),
        ],
        ["awc_r"],
    )
    # 50 cm * 0.20 + 50 cm * 0.10 (clipped at 100) = 15 cm
    result = s.aggregate_available_water_storage(units, parts, layers, "F1")
    assert result.value == pytest.approx(15.0)
    assert result.unit == "cm"
    assert (result.depth_top_cm, result.depth_bottom_cm) == (0.0, 100.0)
    assert result.depth_coverage == pytest.approx(1.0)


def test_available_water_storage_reports_short_profiles():
    units = map_units([("F1", "MU1", 1.0)])
    parts = components([("MU1", "C1", 100.0)], [])
    layers = horizons([("C1", "H1", 0.0, 40.0, 0.15)], ["awc_r"])
    result = s.aggregate_available_water_storage(units, parts, layers, "F1")
    assert result.value == pytest.approx(6.0)
    assert result.depth_coverage == pytest.approx(0.4)


# --- component-level properties ------------------------------------------------------------------
def test_component_property_is_percent_then_area_weighted():
    units = map_units([("F1", "MU1", 0.5), ("F1", "MU2", 0.5)])
    parts = components(
        [
            ("MU1", "C1", 75.0, 2.0),
            ("MU1", "C2", 25.0, 6.0),
            ("MU2", "C3", 100.0, 1.0),
        ],
        ["slope_r"],
    )
    # MU1 = (75*2 + 25*6) / 100 = 3.0; field = 0.5*3.0 + 0.5*1.0 = 2.0
    result = s.aggregate_component_property(units, parts, "F1", "slope_r")
    assert result.value == pytest.approx(2.0)
    assert result.unit == "%"
    assert result.depth_top_cm is None


def test_component_property_ignores_components_without_a_value():
    units = map_units([("F1", "MU1", 1.0)])
    parts = components([("MU1", "C1", 60.0, 4.0), ("MU1", "C2", 40.0, None)], ["slope_r"])
    result = s.aggregate_component_property(units, parts, "F1", "slope_r")
    assert result.value == pytest.approx(4.0)


# --- categorical properties ----------------------------------------------------------------------
def test_class_shares_are_area_and_percent_weighted():
    units = map_units([("F1", "MU1", 0.5), ("F1", "MU2", 0.5)])
    parts = components(
        [
            ("MU1", "C1", 60.0, "Poorly drained"),
            ("MU1", "C2", 40.0, "Well drained"),
            ("MU2", "C3", 100.0, "Well drained"),
        ],
        ["drainagecl"],
    )
    result = s.aggregate_component_class(units, parts, "F1", "drainagecl")
    assert result.status == "ok"
    assert result.shares["Well drained"] == pytest.approx(0.7)
    assert result.shares["Poorly drained"] == pytest.approx(0.3)
    assert result.dominant == "Well drained"
    assert result.dominant_share == pytest.approx(0.7)
    assert sum(result.shares.values()) == pytest.approx(1.0)


def test_dual_hydrologic_group_is_kept_as_one_class():
    units = map_units([("F1", "MU1", 1.0)])
    parts = components([("MU1", "C1", 70.0, "B/D"), ("MU1", "C2", 30.0, "B")], ["hydgrp"])
    result = s.aggregate_component_class(units, parts, "F1", "hydgrp")
    assert set(result.shares) == {"B/D", "B"}
    assert result.shares["B/D"] == pytest.approx(0.7)
    assert result.dominant == "B/D"


def test_class_shares_are_unknown_when_the_area_is_not_weighted():
    units = map_units([("F1", "MU1", None)])
    parts = components([("MU1", "C1", 100.0, "Well drained")], ["drainagecl"])
    result = s.aggregate_component_class(units, parts, "F1", "drainagecl")
    assert result.status == "unknown"
    assert result.dominant is None
    assert result.shares == {}


def test_class_shares_below_the_threshold_keep_the_shares_but_name_no_dominant():
    units = map_units([("F1", "MU1", 0.6), ("F1", "MU2", 0.4)])
    parts = components(
        [("MU1", "C1", 100.0, None), ("MU2", "C3", 100.0, "Well drained")],
        ["drainagecl"],
    )
    result = s.aggregate_component_class(units, parts, "F1", "drainagecl")
    assert result.status == "unknown"
    assert result.dominant is None
    assert result.shares["Well drained"] == pytest.approx(0.4)
    assert result.area_coverage == pytest.approx(0.4)


# --- input checks --------------------------------------------------------------------------------
def test_check_soil_tables_is_quiet_on_clean_input():
    assert s.check_soil_tables(GOLDEN_MAP_UNITS, GOLDEN_COMPONENTS, GOLDEN_HORIZONS) == []


def test_check_soil_tables_reports_area_shares_that_do_not_sum_to_one():
    units = map_units([("F1", "MU1", 0.6), ("F1", "MU2", 0.1)])
    findings = s.check_soil_tables(units, GOLDEN_COMPONENTS, GOLDEN_HORIZONS)
    assert any("not about 1" in finding for finding in findings)


def test_check_soil_tables_reports_null_area_shares():
    units = map_units([("F1", "MU1", 0.6), ("F1", "MU2", None)])
    findings = s.check_soil_tables(units, GOLDEN_COMPONENTS, GOLDEN_HORIZONS)
    assert any("null area_share" in finding for finding in findings)


def test_check_soil_tables_reports_component_percentages_above_one_hundred():
    parts = components([("MU1", "C1", 70.0), ("MU1", "C2", 60.0), ("MU2", "C3", 100.0)], [])
    findings = s.check_soil_tables(GOLDEN_MAP_UNITS, parts, GOLDEN_HORIZONS)
    assert any("above 100" in finding for finding in findings)


def test_check_soil_tables_reports_inverted_depths():
    layers = horizons([("C1", "H1", 30.0, 10.0, 4.0)], ["om_r"])
    findings = s.check_soil_tables(GOLDEN_MAP_UNITS, GOLDEN_COMPONENTS, layers)
    assert any("hzdept_r is not above hzdepb_r" in finding for finding in findings)


def test_check_soil_tables_reports_orphan_map_unit_keys():
    parts = components([("MU_GHOST", "C9", 100.0)], [])
    findings = s.check_soil_tables(GOLDEN_MAP_UNITS, parts, GOLDEN_HORIZONS)
    assert any("absent from map_units" in finding for finding in findings)


def test_check_soil_tables_raises_on_duplicate_keys():
    units = map_units([("F1", "MU1", 0.5), ("F1", "MU1", 0.5)])
    with pytest.raises(ValueError, match="duplicate"):
        s.check_soil_tables(units, GOLDEN_COMPONENTS, GOLDEN_HORIZONS)


def test_check_soil_tables_raises_on_a_missing_column():
    units = pd.DataFrame({"field_id": ["F1"], "mukey": ["MU1"]})
    with pytest.raises(KeyError, match="area_share"):
        s.check_soil_tables(units, GOLDEN_COMPONENTS, GOLDEN_HORIZONS)


# --- lineage -------------------------------------------------------------------------------------
def test_every_soil_property_has_a_complete_lineage_row():
    assert len(s.SOIL_PROPERTY_LINEAGE) == 7
    for row in s.SOIL_PROPERTY_LINEAGE:
        missing = [field for field in s.LINEAGE_FIELDS if not row.get(field)]
        assert not missing, f"{row.get('indicator_id')} is missing {missing}"
        assert row["evidence_type"] == "survey"
        assert "not a lab sample" in row["spatial_scale"]


def test_lineage_ids_are_unique():
    ids = [row["indicator_id"] for row in s.SOIL_PROPERTY_LINEAGE]
    assert len(ids) == len(set(ids))


def test_every_lineage_row_carries_the_survey_caveat():
    for row in s.SOIL_PROPERTY_LINEAGE:
        assert s.SURVEY_CAVEAT in row["limitation"]


def test_texture_lineage_says_components_are_not_renormalised():
    row = next(r for r in s.SOIL_PROPERTY_LINEAGE if r["indicator_id"] == "claytotal_r_0_30cm")
    assert "not re-normalised" in row["limitation"]
