"""SSURGO soil aggregation for a field (AgroCycle, DS2, roadmap Phase 4).

Pure functions over the three tables the DE delivers from USDA Soil Data Access. No I/O, no network.

Input contract (see ``docs/sources/ds2-power-ssurgo-marsden.md``), representative (``_r``) columns only:

    map_units   field_id, mukey, area_share          area_share is the field-area fraction, or null
    components  mukey, cokey, comppct_r, ...         plus slope_r, drainagecl, hydgrp, hydricrating
    horizons    cokey, chkey, hzdept_r, hzdepb_r     plus the property columns, depths in cm

Three weighting stages, each carrying its denominator forward: horizons are thickness-weighted into a
component over a requested depth interval, components are weighted into a map unit by ``comppct_r``, and map
units are weighted into the field by ``area_share``.

What this module refuses to do:

* **Assume area shares.** The sheet's fallback query returns mukeys with no areas. When any share is null the
  result is ``unknown``, because an assumed equal split would invent a soil map.
* **Drop components that have no horizons.** Water and pits carry a ``comppct_r`` and no horizon data. They
  stay in the denominator, so a field that is partly a pond cannot report the organic matter of its dry part
  as the whole field's.
* **Fill anything.** A null property lowers coverage; it never becomes a zero.
* **Average a class.** ``drainagecl``, ``hydgrp`` and ``hydricrating`` return area-weighted shares and a
  dominant class, and dual values such as ``B/D`` are kept verbatim.

Evidence type for every output: ``survey``. Scale: mapped soil units, not a lab sample of the field.
Component percentages describe the map unit, never a location within the field.
"""
from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field as dataclass_field

import pandas as pd

MIN_AREA_COVERAGE = 0.75
# A class is only called dominant if it covers more than half the field. The demo field's most common
# drainage class is 47 %, so calling it "the field's drainage class" would be wrong about 53 % of it.
MAJORITY = 0.5
PLOUGH_LAYER_CM = (0.0, 30.0)
ROOT_ZONE_CM = (0.0, 100.0)

HORIZON_PROPERTY_UNITS = {
    "om_r": "% by weight",
    "claytotal_r": "% by weight",
    "sandtotal_r": "% by weight",
    "silttotal_r": "% by weight",
    "ph1to1h2o_r": "pH",
    "awc_r": "cm/cm",
    "ksat_r": "micrometres/s",
    "dbthirdbar_r": "g/cm3",
    "cec7_r": "meq/100 g",
}
COMPONENT_PROPERTY_UNITS = {
    "slope_r": "%",
    "tfact": "tons/acre/yr",
}
COMPONENT_CLASS_PROPERTIES = ("drainagecl", "hydgrp", "hydricrating")

SURVEY_CAVEAT = (
    "SSURGO is a mapped soil survey, not a lab sample of this field. Component percentages describe the map "
    "unit as a whole and do not locate anything within the field, so a value here is what the survey says "
    "about the units the field intersects."
)


@dataclass(frozen=True)
class SoilProperty:
    """One aggregated numeric soil property for one field, with the area and depth it represents."""

    property_id: str
    value: float | None
    unit: str
    depth_top_cm: float | None
    depth_bottom_cm: float | None
    area_coverage: float
    depth_coverage: float | None
    map_units: int
    status: str
    reason: str | None = None


@dataclass(frozen=True)
class SoilClassShares:
    """Area-weighted shares of a categorical soil class, with the dominant class named."""

    property_id: str
    shares: dict[str, float] = dataclass_field(default_factory=dict)
    dominant: str | None = None
    dominant_share: float | None = None
    area_coverage: float = 0.0
    map_units: int = 0
    status: str = "unknown"
    reason: str | None = None


def _require_columns(frame: pd.DataFrame, columns: list[str], name: str) -> None:
    missing = [column for column in columns if column not in frame.columns]
    if missing:
        raise KeyError(f"{name} is missing required column(s): {', '.join(missing)}")


def check_soil_tables(
    map_units: pd.DataFrame,
    components: pd.DataFrame,
    horizons: pd.DataFrame,
) -> list[str]:
    """Return the sheet's data-quality findings as plain strings; an empty list means nothing to report.

    Structural faults (missing columns, duplicate keys) raise instead, because no weighting of a malformed
    table is meaningful.
    """
    _require_columns(map_units, ["field_id", "mukey", "area_share"], "map_units")
    _require_columns(components, ["mukey", "cokey", "comppct_r"], "components")
    _require_columns(horizons, ["cokey", "chkey", "hzdept_r", "hzdepb_r"], "horizons")

    if map_units.duplicated(subset=["field_id", "mukey"]).any():
        raise ValueError("map_units has duplicate (field_id, mukey) rows")
    if components["cokey"].duplicated().any():
        raise ValueError("components has duplicate cokey rows")
    if horizons["chkey"].duplicated().any():
        raise ValueError("horizons has duplicate chkey rows")

    findings: list[str] = []

    for field_id, group in map_units.groupby("field_id"):
        if group["area_share"].isna().any():
            findings.append(
                f"field {field_id}: {int(group['area_share'].isna().sum())} of {len(group)} map units have a "
                "null area_share, so no area-weighted value can be computed for it"
            )
            continue
        total = float(group["area_share"].sum())
        if abs(total - 1.0) > 0.05:
            findings.append(f"field {field_id}: area shares sum to {total:.3f}, not about 1")

    out_of_range = components["comppct_r"].dropna()
    if ((out_of_range < 0) | (out_of_range > 100)).any():
        findings.append("components: comppct_r outside 0-100")
    for mukey, group in components.groupby("mukey"):
        total = float(group["comppct_r"].fillna(0).sum())
        if total > 100.5:
            findings.append(f"map unit {mukey}: component percentages sum to {total:.1f}, above 100")

    depths = horizons.dropna(subset=["hzdept_r", "hzdepb_r"])
    bad_depths = depths.loc[depths["hzdept_r"] >= depths["hzdepb_r"], "chkey"]
    if len(bad_depths):
        findings.append(f"horizons: {len(bad_depths)} row(s) where hzdept_r is not above hzdepb_r")

    orphans = set(components["mukey"]) - set(map_units["mukey"])
    if orphans:
        findings.append(f"components reference {len(orphans)} mukey(s) absent from map_units")

    return findings


def _overlap_cm(top: float, bottom: float, depth_top: float, depth_bottom: float) -> float:
    return max(0.0, min(bottom, depth_bottom) - max(top, depth_top))


def component_depth_weighted_value(
    horizons: pd.DataFrame,
    cokey: str,
    property_column: str,
    depth_top_cm: float,
    depth_bottom_cm: float,
) -> tuple[float | None, float]:
    """Thickness-weighted mean of a horizon property for one component over a depth interval.

    Returns the value (or None) and the thickness in cm that carried data. Horizons with a null depth or a
    null property contribute nothing and are not estimated from their neighbours.
    """
    if depth_bottom_cm <= depth_top_cm:
        raise ValueError(f"depth_bottom_cm {depth_bottom_cm} must exceed depth_top_cm {depth_top_cm}")
    _require_columns(horizons, ["cokey", "hzdept_r", "hzdepb_r", property_column], "horizons")

    rows = horizons.loc[horizons["cokey"] == cokey]
    weighted_total = 0.0
    thickness_total = 0.0
    for _, row in rows.iterrows():
        top, bottom, value = row["hzdept_r"], row["hzdepb_r"], row[property_column]
        if pd.isna(top) or pd.isna(bottom) or pd.isna(value) or bottom <= top:
            continue
        thickness = _overlap_cm(float(top), float(bottom), depth_top_cm, depth_bottom_cm)
        if thickness <= 0:
            continue
        weighted_total += thickness * float(value)
        thickness_total += thickness

    if thickness_total <= 0:
        return None, 0.0
    return weighted_total / thickness_total, thickness_total


def component_available_water_storage(
    horizons: pd.DataFrame,
    cokey: str,
    depth_top_cm: float,
    depth_bottom_cm: float,
) -> tuple[float | None, float]:
    """Available water storage in cm for one component: sum of thickness x awc_r over the interval."""
    if depth_bottom_cm <= depth_top_cm:
        raise ValueError(f"depth_bottom_cm {depth_bottom_cm} must exceed depth_top_cm {depth_top_cm}")
    _require_columns(horizons, ["cokey", "hzdept_r", "hzdepb_r", "awc_r"], "horizons")

    rows = horizons.loc[horizons["cokey"] == cokey]
    storage = 0.0
    thickness_total = 0.0
    for _, row in rows.iterrows():
        top, bottom, awc = row["hzdept_r"], row["hzdepb_r"], row["awc_r"]
        if pd.isna(top) or pd.isna(bottom) or pd.isna(awc) or bottom <= top:
            continue
        thickness = _overlap_cm(float(top), float(bottom), depth_top_cm, depth_bottom_cm)
        if thickness <= 0:
            continue
        storage += thickness * float(awc)
        thickness_total += thickness

    if thickness_total <= 0:
        return None, 0.0
    return storage, thickness_total


def _field_map_units(map_units: pd.DataFrame, field_id: str) -> pd.DataFrame:
    rows = map_units.loc[map_units["field_id"] == field_id]
    if rows.empty:
        raise ValueError(f"no map units for field {field_id}; a field with no soil map is a geometry problem")
    return rows


def _unknown_property(
    property_id: str,
    unit: str,
    depth: tuple[float, float] | None,
    map_unit_count: int,
    reason: str,
    area_coverage: float = 0.0,
) -> SoilProperty:
    return SoilProperty(
        property_id=property_id,
        value=None,
        unit=unit,
        depth_top_cm=depth[0] if depth else None,
        depth_bottom_cm=depth[1] if depth else None,
        area_coverage=area_coverage,
        depth_coverage=None,
        map_units=map_unit_count,
        status="unknown",
        reason=reason,
    )


def _null_share_reason(rows: pd.DataFrame) -> str | None:
    null_count = int(rows["area_share"].isna().sum())
    if not null_count:
        return None
    return (
        f"{null_count} of {len(rows)} map units have no area_share, so the field cannot be area-weighted; "
        "equal weights are not assumed"
    )


def aggregate_horizon_property(
    map_units: pd.DataFrame,
    components: pd.DataFrame,
    horizons: pd.DataFrame,
    field_id: str,
    property_column: str,
    depth_cm: tuple[float, float] = PLOUGH_LAYER_CM,
    unit: str | None = None,
    min_area_coverage: float = MIN_AREA_COVERAGE,
) -> SoilProperty:
    """Aggregate a horizon property to the field: thickness, then comppct_r, then area_share."""
    rows = _field_map_units(map_units, field_id)
    resolved_unit = unit or HORIZON_PROPERTY_UNITS.get(property_column, "unknown unit")
    property_id = f"{property_column}_{int(depth_cm[0])}_{int(depth_cm[1])}cm"
    null_reason = _null_share_reason(rows)
    if null_reason:
        return _unknown_property(property_id, resolved_unit, depth_cm, len(rows), null_reason)

    area_total = float(rows["area_share"].sum())
    if area_total <= 0:
        return _unknown_property(
            property_id, resolved_unit, depth_cm, len(rows), "map unit area shares sum to zero"
        )

    requested_thickness = depth_cm[1] - depth_cm[0]
    area_weighted_value = 0.0
    area_with_value = 0.0
    area_weighted_depth = 0.0

    for _, map_unit in rows.iterrows():
        unit_components = components.loc[components["mukey"] == map_unit["mukey"]]
        percent_total = float(unit_components["comppct_r"].fillna(0).sum())
        if percent_total <= 0:
            continue

        value_weighted = 0.0
        percent_with_value = 0.0
        depth_weighted = 0.0
        for _, component in unit_components.iterrows():
            percent = component["comppct_r"]
            if pd.isna(percent) or float(percent) <= 0:
                continue
            value, thickness = component_depth_weighted_value(
                horizons, component["cokey"], property_column, depth_cm[0], depth_cm[1]
            )
            if value is None:
                # Water, pits and components with no horizon data stay in percent_total below.
                continue
            value_weighted += float(percent) * value
            percent_with_value += float(percent)
            depth_weighted += float(percent) * min(1.0, thickness / requested_thickness)

        if percent_with_value <= 0:
            continue
        share = float(map_unit["area_share"])
        area_weighted_value += share * (value_weighted / percent_with_value)
        # Divided by the map unit's whole component percentage, so horizon-less components count against it.
        area_weighted_depth += share * (depth_weighted / percent_total)
        area_with_value += share

    area_coverage = area_with_value / area_total
    if area_with_value <= 0:
        return _unknown_property(
            property_id,
            resolved_unit,
            depth_cm,
            len(rows),
            f"no component in any map unit reports {property_column} in {depth_cm[0]:g}-{depth_cm[1]:g} cm",
        )
    if area_coverage < min_area_coverage:
        return _unknown_property(
            property_id,
            resolved_unit,
            depth_cm,
            len(rows),
            (
                f"only {area_coverage:.0%} of the field's mapped area reports {property_column}; "
                f"below the {min_area_coverage:.0%} required"
            ),
            area_coverage=area_coverage,
        )

    return SoilProperty(
        property_id=property_id,
        value=area_weighted_value / area_with_value,
        unit=resolved_unit,
        depth_top_cm=depth_cm[0],
        depth_bottom_cm=depth_cm[1],
        area_coverage=area_coverage,
        depth_coverage=area_weighted_depth / area_total,
        map_units=len(rows),
        status="ok",
    )


def aggregate_available_water_storage(
    map_units: pd.DataFrame,
    components: pd.DataFrame,
    horizons: pd.DataFrame,
    field_id: str,
    depth_cm: tuple[float, float] = ROOT_ZONE_CM,
    min_area_coverage: float = MIN_AREA_COVERAGE,
) -> SoilProperty:
    """Available water storage in cm over the interval, aggregated to the field."""
    rows = _field_map_units(map_units, field_id)
    property_id = f"available_water_storage_{int(depth_cm[0])}_{int(depth_cm[1])}cm"
    null_reason = _null_share_reason(rows)
    if null_reason:
        return _unknown_property(property_id, "cm", depth_cm, len(rows), null_reason)

    area_total = float(rows["area_share"].sum())
    if area_total <= 0:
        return _unknown_property(
            property_id, "cm", depth_cm, len(rows), "map unit area shares sum to zero"
        )

    requested_thickness = depth_cm[1] - depth_cm[0]
    area_weighted_value = 0.0
    area_with_value = 0.0
    area_weighted_depth = 0.0

    for _, map_unit in rows.iterrows():
        unit_components = components.loc[components["mukey"] == map_unit["mukey"]]
        percent_total = float(unit_components["comppct_r"].fillna(0).sum())
        if percent_total <= 0:
            continue

        value_weighted = 0.0
        percent_with_value = 0.0
        depth_weighted = 0.0
        for _, component in unit_components.iterrows():
            percent = component["comppct_r"]
            if pd.isna(percent) or float(percent) <= 0:
                continue
            storage, thickness = component_available_water_storage(
                horizons, component["cokey"], depth_cm[0], depth_cm[1]
            )
            if storage is None:
                continue
            value_weighted += float(percent) * storage
            percent_with_value += float(percent)
            depth_weighted += float(percent) * min(1.0, thickness / requested_thickness)

        if percent_with_value <= 0:
            continue
        share = float(map_unit["area_share"])
        area_weighted_value += share * (value_weighted / percent_with_value)
        area_weighted_depth += share * (depth_weighted / percent_total)
        area_with_value += share

    area_coverage = area_with_value / area_total
    if area_with_value <= 0:
        return _unknown_property(
            property_id, "cm", depth_cm, len(rows), "no component reports awc_r in the interval"
        )
    if area_coverage < min_area_coverage:
        return _unknown_property(
            property_id,
            "cm",
            depth_cm,
            len(rows),
            (
                f"only {area_coverage:.0%} of the field's mapped area reports awc_r; "
                f"below the {min_area_coverage:.0%} required"
            ),
            area_coverage=area_coverage,
        )

    return SoilProperty(
        property_id=property_id,
        value=area_weighted_value / area_with_value,
        unit="cm",
        depth_top_cm=depth_cm[0],
        depth_bottom_cm=depth_cm[1],
        area_coverage=area_coverage,
        depth_coverage=area_weighted_depth / area_total,
        map_units=len(rows),
        status="ok",
    )


def aggregate_component_property(
    map_units: pd.DataFrame,
    components: pd.DataFrame,
    field_id: str,
    property_column: str,
    unit: str | None = None,
    min_area_coverage: float = MIN_AREA_COVERAGE,
) -> SoilProperty:
    """Aggregate a component-level numeric property (such as slope_r) to the field."""
    rows = _field_map_units(map_units, field_id)
    _require_columns(components, ["mukey", "comppct_r", property_column], "components")
    resolved_unit = unit or COMPONENT_PROPERTY_UNITS.get(property_column, "unknown unit")
    null_reason = _null_share_reason(rows)
    if null_reason:
        return _unknown_property(property_column, resolved_unit, None, len(rows), null_reason)

    area_total = float(rows["area_share"].sum())
    if area_total <= 0:
        return _unknown_property(
            property_column, resolved_unit, None, len(rows), "map unit area shares sum to zero"
        )

    area_weighted_value = 0.0
    area_with_value = 0.0
    for _, map_unit in rows.iterrows():
        unit_components = components.loc[components["mukey"] == map_unit["mukey"]]
        usable = unit_components.dropna(subset=["comppct_r", property_column])
        percent_with_value = float(usable["comppct_r"].sum())
        if percent_with_value <= 0:
            continue
        weighted = float((usable["comppct_r"] * usable[property_column]).sum())
        share = float(map_unit["area_share"])
        area_weighted_value += share * (weighted / percent_with_value)
        area_with_value += share

    area_coverage = area_with_value / area_total
    if area_with_value <= 0:
        return _unknown_property(
            property_column, resolved_unit, None, len(rows), f"no component reports {property_column}"
        )
    if area_coverage < min_area_coverage:
        return _unknown_property(
            property_column,
            resolved_unit,
            None,
            len(rows),
            (
                f"only {area_coverage:.0%} of the field's mapped area reports {property_column}; "
                f"below the {min_area_coverage:.0%} required"
            ),
            area_coverage=area_coverage,
        )

    return SoilProperty(
        property_id=property_column,
        value=area_weighted_value / area_with_value,
        unit=resolved_unit,
        depth_top_cm=None,
        depth_bottom_cm=None,
        area_coverage=area_coverage,
        depth_coverage=None,
        map_units=len(rows),
        status="ok",
    )


def aggregate_component_class(
    map_units: pd.DataFrame,
    components: pd.DataFrame,
    field_id: str,
    property_column: str,
    min_area_coverage: float = MIN_AREA_COVERAGE,
) -> SoilClassShares:
    """Area-weighted share of each class of a categorical component property.

    Classes are never averaged or merged: a dual hydrologic group such as ``B/D`` stays its own class, because
    resolving it would require drainage information SSURGO does not give here.
    """
    rows = _field_map_units(map_units, field_id)
    _require_columns(components, ["mukey", "comppct_r", property_column], "components")
    null_reason = _null_share_reason(rows)
    if null_reason:
        return SoilClassShares(
            property_id=property_column, map_units=len(rows), status="unknown", reason=null_reason
        )

    area_total = float(rows["area_share"].sum())
    if area_total <= 0:
        return SoilClassShares(
            property_id=property_column,
            map_units=len(rows),
            status="unknown",
            reason="map unit area shares sum to zero",
        )

    shares: dict[str, float] = {}
    area_with_value = 0.0
    for _, map_unit in rows.iterrows():
        unit_components = components.loc[components["mukey"] == map_unit["mukey"]]
        usable = unit_components.dropna(subset=["comppct_r", property_column])
        percent_with_value = float(usable["comppct_r"].sum())
        if percent_with_value <= 0:
            continue
        share = float(map_unit["area_share"])
        for _, component in usable.iterrows():
            label = str(component[property_column])
            weight = share * float(component["comppct_r"]) / percent_with_value
            shares[label] = shares.get(label, 0.0) + weight
        area_with_value += share

    area_coverage = area_with_value / area_total
    if area_with_value <= 0:
        return SoilClassShares(
            property_id=property_column,
            map_units=len(rows),
            status="unknown",
            reason=f"no component reports {property_column}",
        )

    normalised = {label: weight / area_total for label, weight in shares.items()}
    largest = max(normalised, key=normalised.get)
    if area_coverage < min_area_coverage:
        return SoilClassShares(
            property_id=property_column,
            shares=normalised,
            dominant=None,
            dominant_share=None,
            area_coverage=area_coverage,
            map_units=len(rows),
            status="unknown",
            reason=(
                f"only {area_coverage:.0%} of the field's mapped area reports {property_column}; "
                f"below the {min_area_coverage:.0%} required"
            ),
        )

    if normalised[largest] <= MAJORITY:
        return SoilClassShares(
            property_id=property_column,
            shares=normalised,
            dominant=None,
            dominant_share=None,
            area_coverage=area_coverage,
            map_units=len(rows),
            status="ok",
            reason=(
                f"no class covers more than half the field: the largest is {largest!r} at "
                f"{normalised[largest]:.0%}, so the field is mixed and the shares are the answer"
            ),
        )

    return SoilClassShares(
        property_id=property_column,
        shares=normalised,
        dominant=largest,
        dominant_share=normalised[largest],
        area_coverage=area_coverage,
        map_units=len(rows),
        status="ok",
    )


_SOURCE = "USDA SSURGO via Soil Data Access (SDA) tabular REST service"
_SOURCE_URL = "https://sdmdataaccess.sc.egov.usda.gov/Tabular/post.rest"
_SCALE = (
    "Mapped soil units intersecting the field polygon, not a lab sample of the field. Component percentages "
    "describe the map unit and do not locate anything within the field."
)
_MISSING_RULE = (
    "Nothing is filled. A null property lowers coverage rather than becoming a zero, components with no "
    "horizons stay in the map unit's denominator, and a null area_share makes the field value 'unknown' "
    "because equal weights are never assumed."
)

SOIL_PROPERTY_LINEAGE = [
    {
        "indicator_id": "om_r_0_30cm",
        "variables": ["om_r", "hzdept_r", "hzdepb_r", "comppct_r", "area_share"],
        "formula": (
            "thickness-weighted mean of om_r over 0-30 cm per component, comppct_r-weighted to the map unit, "
            "area_share-weighted to the field"
        ),
        "unit": "% by weight",
        "evidence_type": "survey",
        "source": _SOURCE,
        "source_url": _SOURCE_URL,
        "spatial_scale": _SCALE,
        "temporal_window": "survey area version date from sacatalog; not a dated measurement",
        "missing_data_rule": _MISSING_RULE,
        "limitation": (
            f"{SURVEY_CAVEAT} The 0-30 cm interval is a conventional plough layer, not a calibrated depth. "
            "Organic matter from a survey cannot show change over time or the effect of management."
        ),
    },
    {
        "indicator_id": "claytotal_r_0_30cm",
        "variables": ["claytotal_r", "hzdept_r", "hzdepb_r", "comppct_r", "area_share"],
        "formula": "as om_r_0_30cm, for claytotal_r",
        "unit": "% by weight",
        "evidence_type": "survey",
        "source": _SOURCE,
        "source_url": _SOURCE_URL,
        "spatial_scale": _SCALE,
        "temporal_window": "survey area version date from sacatalog; not a dated measurement",
        "missing_data_rule": _MISSING_RULE,
        "limitation": (
            f"{SURVEY_CAVEAT} Clay, sand and silt are aggregated independently, so the three need not sum to "
            "100 after weighting; they are not re-normalised, because that would hide missing horizons."
        ),
    },
    {
        "indicator_id": "awc_r_0_100cm",
        "variables": ["awc_r", "hzdept_r", "hzdepb_r", "comppct_r", "area_share"],
        "formula": "as om_r_0_30cm, for awc_r over 0-100 cm",
        "unit": "cm/cm",
        "evidence_type": "survey",
        "source": _SOURCE,
        "source_url": _SOURCE_URL,
        "spatial_scale": _SCALE,
        "temporal_window": "survey area version date from sacatalog; not a dated measurement",
        "missing_data_rule": _MISSING_RULE,
        "limitation": (
            f"{SURVEY_CAVEAT} A mean of cm/cm is not a storage figure; use "
            "available_water_storage_0_100cm for depth-integrated storage."
        ),
    },
    {
        "indicator_id": "available_water_storage_0_100cm",
        "variables": ["awc_r", "hzdept_r", "hzdepb_r", "comppct_r", "area_share"],
        "formula": (
            "sum of horizon thickness x awc_r over 0-100 cm per component, comppct_r-weighted to the map "
            "unit, area_share-weighted to the field"
        ),
        "unit": "cm",
        "evidence_type": "survey",
        "source": _SOURCE,
        "source_url": _SOURCE_URL,
        "spatial_scale": _SCALE,
        "temporal_window": "survey area version date from sacatalog; not a dated measurement",
        "missing_data_rule": (
            f"{_MISSING_RULE} A component whose horizons stop short of 100 cm reports storage for the depth "
            "it covers, and depth_coverage says how much that was."
        ),
        "limitation": (
            f"{SURVEY_CAVEAT} Plant-available water also depends on rooting depth, compaction and crop, none "
            "of which is here. A root zone of 0-100 cm is an assumption, not a measurement."
        ),
    },
    {
        "indicator_id": "slope_r",
        "variables": ["slope_r", "comppct_r", "area_share"],
        "formula": "comppct_r-weighted mean of component slope_r, area_share-weighted to the field",
        "unit": "%",
        "evidence_type": "survey",
        "source": _SOURCE,
        "source_url": _SOURCE_URL,
        "spatial_scale": _SCALE,
        "temporal_window": "survey area version date from sacatalog; not a dated measurement",
        "missing_data_rule": _MISSING_RULE,
        "limitation": (
            f"{SURVEY_CAVEAT} A representative slope for a map unit is not the field's slope distribution, and "
            "no erosion claim follows from it without a defensible method."
        ),
    },
    {
        "indicator_id": "drainagecl",
        "variables": ["drainagecl", "comppct_r", "area_share"],
        "formula": "area- and comppct_r-weighted share of each drainage class; dominant class named",
        "unit": "share of field area per class",
        "evidence_type": "survey",
        "source": _SOURCE,
        "source_url": _SOURCE_URL,
        "spatial_scale": _SCALE,
        "temporal_window": "survey area version date from sacatalog; not a dated measurement",
        "missing_data_rule": _MISSING_RULE,
        "limitation": (
            f"{SURVEY_CAVEAT} A dominant class with a small share is not a drainage class for the field, so "
            "the shares must be shown alongside it. Installed tile drainage is not in SSURGO."
        ),
    },
    {
        "indicator_id": "hydgrp",
        "variables": ["hydgrp", "comppct_r", "area_share"],
        "formula": "area- and comppct_r-weighted share of each hydrologic group; dual values kept verbatim",
        "unit": "share of field area per class",
        "evidence_type": "survey",
        "source": _SOURCE,
        "source_url": _SOURCE_URL,
        "spatial_scale": _SCALE,
        "temporal_window": "survey area version date from sacatalog; not a dated measurement",
        "missing_data_rule": _MISSING_RULE,
        "limitation": (
            f"{SURVEY_CAVEAT} A dual group such as B/D means drained versus undrained and is kept as one "
            "string; resolving it needs drainage information this source does not provide."
        ),
    },
    {
        "indicator_id": "sandtotal_r_0_30cm",
        "variables": ["sandtotal_r", "hzdept_r", "hzdepb_r", "comppct_r", "area_share"],
        "formula": "as om_r_0_30cm, for sandtotal_r",
        "unit": "% by weight",
        "evidence_type": "survey",
        "source": _SOURCE,
        "source_url": _SOURCE_URL,
        "spatial_scale": _SCALE,
        "temporal_window": "survey area version date from sacatalog; not a dated measurement",
        "missing_data_rule": _MISSING_RULE,
        "limitation": (
            f"{SURVEY_CAVEAT} Sand, silt and clay are aggregated independently and are not re-normalised to "
            "sum to 100, because that would hide missing horizons."
        ),
    },
    {
        "indicator_id": "silttotal_r_0_30cm",
        "variables": ["silttotal_r", "hzdept_r", "hzdepb_r", "comppct_r", "area_share"],
        "formula": "as om_r_0_30cm, for silttotal_r",
        "unit": "% by weight",
        "evidence_type": "survey",
        "source": _SOURCE,
        "source_url": _SOURCE_URL,
        "spatial_scale": _SCALE,
        "temporal_window": "survey area version date from sacatalog; not a dated measurement",
        "missing_data_rule": _MISSING_RULE,
        "limitation": (
            f"{SURVEY_CAVEAT} Sand, silt and clay are aggregated independently and are not re-normalised to "
            "sum to 100, because that would hide missing horizons."
        ),
    },
    {
        "indicator_id": "ph1to1h2o_r_0_30cm",
        "variables": ["ph1to1h2o_r", "hzdept_r", "hzdepb_r", "comppct_r", "area_share"],
        "formula": "as om_r_0_30cm, for ph1to1h2o_r",
        "unit": "pH",
        "evidence_type": "survey",
        "source": _SOURCE,
        "source_url": _SOURCE_URL,
        "spatial_scale": _SCALE,
        "temporal_window": "survey area version date from sacatalog; not a dated measurement",
        "missing_data_rule": _MISSING_RULE,
        "limitation": (
            f"{SURVEY_CAVEAT} A survey pH is not a current soil test. pH responds to liming and management "
            "within a season, and averaging a logarithmic scale across map units is approximate."
        ),
    },
    {
        "indicator_id": "drainagecl_dominant",
        "variables": ["drainagecl", "comppct_r", "area_share"],
        "formula": "field-area share of the most common drainage class",
        "unit": "% of field area",
        "evidence_type": "survey",
        "source": _SOURCE,
        "source_url": _SOURCE_URL,
        "spatial_scale": _SCALE,
        "temporal_window": "survey area version date from sacatalog; not a dated measurement",
        "missing_data_rule": _MISSING_RULE,
        "limitation": (
            f"{SURVEY_CAVEAT} The most common class is often not a majority: on the primary demo field it is "
            "47 %, so most of the field is something else. This value is meaningless without the full set of "
            "class shares beside it, which is why they are loaded too. Installed tile drainage is not in "
            "SSURGO."
        ),
    },
    {
        "indicator_id": "hydgrp_dominant",
        "variables": ["hydgrp", "comppct_r", "area_share"],
        "formula": "field-area share of the most common hydrologic group",
        "unit": "% of field area",
        "evidence_type": "survey",
        "source": _SOURCE,
        "source_url": _SOURCE_URL,
        "spatial_scale": _SCALE,
        "temporal_window": "survey area version date from sacatalog; not a dated measurement",
        "missing_data_rule": _MISSING_RULE,
        "limitation": (
            f"{SURVEY_CAVEAT} As for drainage, the most common group need not be a majority, and a dual "
            "group such as B/D is kept whole because resolving it needs drainage information this source "
            "does not provide."
        ),
    },
    {
        "indicator_id": "map_unit_share",
        "variables": ["mukey", "area_share"],
        "formula": (
            "intersection area of each soil map unit with the field polygon, computed in EPSG:5070, divided "
            "by the total intersected area"
        ),
        "unit": "% of field area",
        "evidence_type": "survey",
        "source": _SOURCE,
        "source_url": _SOURCE_URL,
        "spatial_scale": _SCALE,
        "temporal_window": "survey area version date from sacatalog; not a dated measurement",
        "missing_data_rule": (
            "A field whose map units have no area is reported as unknown; equal shares are never assumed."
        ),
        "limitation": (
            f"{SURVEY_CAVEAT} These are the shares every other soil value is weighted by, so they are the "
            "audit trail for the aggregates. Small slivers are kept: they move the result by almost nothing, "
            "but dropping them would change the denominator."
        ),
    },
]

LINEAGE_FIELDS = (
    "indicator_id",
    "variables",
    "formula",
    "unit",
    "evidence_type",
    "source",
    "source_url",
    "spatial_scale",
    "temporal_window",
    "missing_data_rule",
    "limitation",
)
