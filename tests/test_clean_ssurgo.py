"""SSURGO cleaning: the committed primary-001 sample, and synthetic tables that break each of DS2's checks."""

import json
from pathlib import Path

import pytest

from transform.clean import ssurgo
from transform.indicators import soil as s

SAMPLE = Path(__file__).resolve().parent.parent / "data" / "sample" / "primary-001" / "ssurgo"

# two adjacent 0.001-degree squares in Story County: equal areas, so shares of 0.5 each
LEFT = "POLYGON ((-93.600 42.000, -93.600 42.001, -93.599 42.001, -93.599 42.000, -93.600 42.000))"
RIGHT = "POLYGON ((-93.599 42.000, -93.599 42.001, -93.598 42.001, -93.598 42.000, -93.599 42.000))"
STEP_A = [["mukey", "isect_wkt"], ["1", LEFT], ["2", RIGHT]]
STEP_B = [
    ["mukey", "muname", "cokey", "comppct_r", "slope_r"],
    ["1", "Alpha", "10", "60", "2"], ["1", "Alpha", "11", "40", "3"],
    ["2", "Beta", "20", "100", "1"],
]
STEP_C = [
    ["cokey", "chkey", "hzname", "hzdept_r", "hzdepb_r", "om_r"],
    ["10", "100", "Ap", "0", "30", "3.0"], ["10", "101", "Bt", "30", "100", "1.0"],
    ["11", "110", "Ap", "0", "25", "2.0"],
    ["20", "200", "Ap", "0", "30", "4.0"],
]


def load_sample(name):
    return json.loads((SAMPLE / f"{name}.json").read_text())["Table"]


def clean(a=STEP_A, b=STEP_B, c=STEP_C):
    return ssurgo.clean_field("f", a, b, c)


def test_the_primary_field_sample_is_clean_and_nothing_is_dropped():
    result = ssurgo.clean_field(
        "primary-001", load_sample("step_a_map_units"), load_sample("step_b_components"), load_sample("step_c_horizons")
    )
    assert (len(result.map_units), len(result.components), len(result.horizons)) == (10, 30, 114)
    assert result.findings == []
    assert abs(result.map_units["area_share"].sum() - 1) < 1e-3
    assert s.check_soil_tables(result.map_units, result.components, result.horizons) == []  # DS2's check agrees


def test_a_clean_synthetic_field_has_equal_shares_and_no_findings():
    result = clean()
    assert result.findings == [] and list(result.map_units["area_share"].round(2)) == [0.5, 0.5]


def test_a_horizon_whose_top_is_not_above_its_bottom_is_a_finding():
    bad = [r[:] for r in STEP_C]
    bad[1][3], bad[1][4] = "30", "30"
    result = clean(c=bad)
    assert any("top is not above the bottom" in f for f in result.findings)
    assert s.check_soil_tables(result.map_units, result.components, result.horizons)  # DS2 flags it too


def test_overlapping_horizons_are_a_finding():
    bad = [r[:] for r in STEP_C]
    bad[2][3] = "20"  # the Bt now starts at 20 cm, inside the Ap (0-30)
    assert any("overlap" in f for f in clean(c=bad).findings)


def test_comppct_outside_0_to_100_and_sums_over_100_are_findings():
    bad = [r[:] for r in STEP_B]
    bad[1][3] = "120"
    findings = clean(b=bad).findings
    assert any("outside 0-100" in f for f in findings) and any("over 100" in f for f in findings)
    over = [r[:] for r in STEP_B]
    over[1][3], over[2][3] = "70", "50"  # each is valid; map unit 1 sums to 120
    assert any("map unit 1 components sum to 120" in f for f in clean(b=over).findings)


def test_a_single_map_unit_gets_the_whole_field_and_bad_shares_are_findings_never_fixed():
    result = clean(a=[["mukey", "isect_wkt"], ["1", LEFT]])
    assert result.findings == [] and float(result.map_units["area_share"].iloc[0]) == pytest.approx(1.0)
    # the sheet's fallback query returns no geometry: a null share, never an assumed equal split
    assert ssurgo._share_findings("f", result.map_units.assign(area_share=[None])) == [
        "f: 1 of 1 map units have no area share"
    ]
    assert any("sum to" in f for f in ssurgo._share_findings("f", result.map_units.assign(area_share=[0.8])))


def test_low_and_high_columns_are_refused():
    bad = [STEP_C[0] + ["om_l"]] + [r + ["1"] for r in STEP_C[1:]]
    with pytest.raises(ValueError, match="representative"):
        clean(c=bad)


def test_a_field_with_no_map_unit_stops_with_a_message_for_ds2():
    with pytest.raises(ValueError, match="geometry or CRS"):
        clean(a=[["mukey", "isect_wkt"]])


def test_components_without_horizons_and_null_properties_are_kept():
    only_one = [STEP_C[0], STEP_C[1]]  # components 11 and 20 now have no horizons (water, pits)
    result = clean(c=only_one)
    assert len(result.components) == 3 and len(result.horizons) == 1 and result.findings == []
