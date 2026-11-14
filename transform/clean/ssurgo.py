"""Clean SSURGO Soil Data Access responses for one field (roadmap Phase 4, DE; rules from DS2's sheet, section 2).

Tidy frames, one row per (field, map unit), per component and per horizon. Nothing is dropped, filled or
reweighted: that is DS2's work. Area shares use DS2's `soil_tables`, so there is one implementation of the
equal-area geometry maths; the checks below are the DE's own and are compared with hers in the tests.

Findings are reported, not fixed. A field with no map unit at all is a geometry or CRS problem and stops.
"""

import re
from dataclasses import dataclass, field

import pandas as pd

from transform.indicators.runner import soil_tables

SHARE_TOLERANCE = 0.001  # field area shares must sum to 1 within this
PERCENT_TOLERANCE = 1e-6
LOW_HIGH_COLUMN = re.compile(r"_[lh]$")  # DS2's sheet: representative (_r) values only


@dataclass
class SoilResult:
    field_id: str
    map_units: pd.DataFrame
    components: pd.DataFrame
    horizons: pd.DataFrame
    findings: list[str] = field(default_factory=list)


def _columns(table: list[list]) -> list[str]:
    return list(table[0])


def clean_field(field_id: str, step_a: list[list], step_b: list[list], step_c: list[list]) -> SoilResult:
    for name, table in (("step_a", step_a), ("step_b", step_b), ("step_c", step_c)):
        banned = [c for c in _columns(table) if LOW_HIGH_COLUMN.search(c)]
        if banned:
            raise ValueError(f"{field_id} {name}: low/high columns {banned}; only representative (_r) values are used")
    if len(step_a) < 2:
        raise ValueError(f"{field_id}: no map unit intersects the polygon (a geometry or CRS problem; tell DS2)")

    map_units, components, horizons = soil_tables(field_id, step_a, step_b, step_c)
    findings = []
    if len(components) != len(step_b) - 1 or len(horizons) != len(step_c) - 1:
        findings.append(f"{field_id}: rows were dropped (components {len(step_b) - 1} to {len(components)}, "
                        f"horizons {len(step_c) - 1} to {len(horizons)})")
    findings += _share_findings(field_id, map_units)
    findings += _component_findings(field_id, components)
    findings += _horizon_findings(field_id, components, horizons)
    return SoilResult(field_id, map_units, components, horizons, findings)


def _share_findings(field_id: str, map_units: pd.DataFrame) -> list[str]:
    shares = map_units["area_share"]
    if shares.isna().any():
        return [f"{field_id}: {int(shares.isna().sum())} of {len(map_units)} map units have no area share"]
    total = float(shares.sum())
    if abs(total - 1.0) > SHARE_TOLERANCE:
        return [f"{field_id}: area shares sum to {total:.4f}, not 1"]
    return []


def _component_findings(field_id: str, components: pd.DataFrame) -> list[str]:
    found = []
    pct = components["comppct_r"]
    bad = components[(pct < 0) | (pct > 100)]
    if len(bad):
        found.append(f"{field_id}: {len(bad)} components with comppct_r outside 0-100")
    over = components.groupby("mukey")["comppct_r"].sum()
    for mukey, total in over[over > 100 + PERCENT_TOLERANCE].items():
        found.append(f"{field_id}: map unit {mukey} components sum to {total:g} %, over 100")
    return found


def _horizon_findings(field_id: str, components: pd.DataFrame, horizons: pd.DataFrame) -> list[str]:
    found = []
    inverted = horizons[horizons["hzdept_r"] >= horizons["hzdepb_r"]]
    if len(inverted):
        found.append(f"{field_id}: {len(inverted)} horizons whose top is not above the bottom")
    ordered = horizons.sort_values(["cokey", "hzdept_r"])
    previous_bottom = ordered.groupby("cokey")["hzdepb_r"].shift()
    overlap = ordered[ordered["hzdept_r"] < previous_bottom]
    if len(overlap):
        found.append(f"{field_id}: {len(overlap)} horizons overlap the one above them")
    return found
