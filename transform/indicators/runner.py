"""Compute field indicators for every field from the raw POWER and SSURGO pulls.

AgroCycle, DS2, roadmap Phase 4. Turns the DE's raw S3 objects into the three tables the app reads:
``field_indicators``, ``soil_properties`` and ``indicator_lineage``, written as CSV for the DE to load.

The computation itself lives in ``climate.py`` and ``soil.py`` and stays pure; this module is the thin
shell around it — read, loop, map onto the ClickHouse column names, write.

Usage from the repository root:

    uv run python -m transform.indicators.runner                      # every field, from S3
    uv run python -m transform.indicators.runner --fields primary-001 # one field
    uv run python -m transform.indicators.runner --local DIR          # from a local copy of raw/

Status mapping, which the UI depends on: an indicator with every day present is ``available``; one computed
from fewer days than the window holds is ``partial``, so a thin but usable series cannot pass as complete;
one below the coverage threshold is ``unknown`` and carries the reason.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
import uuid
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import shapely
from pyproj import Transformer
from shapely import wkt

from transform.indicators import climate as c
from transform.indicators import soil as s

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUT = REPO_ROOT / "data" / "out" / "indicators"
FIELDS_PATH = REPO_ROOT / "data" / "fields" / "fields.geojson"

POWER_PREFIX = "raw/power/daily-point-api-v2.10.3/2026-11-14"
SSURGO_PREFIX = "raw/ssurgo/soil-data-access/2026-11-14"
POWER_SUFFIX = "_19910101-20251231.json"
MARSDEN_POINT = "marsden-site"

SEASON_START = (4, 1)
SEASON_END = (11, 30)
FIRST_SEASON = 2015
LAST_SEASON = 2025
AREA_CRS = "EPSG:5070"

SOIL_DEPTH_PROPERTIES = tuple(
    (column, s.PLOUGH_LAYER_CM)
    for column in ("om_r", "claytotal_r", "sandtotal_r", "silttotal_r", "ph1to1h2o_r")
)
SOIL_CLASS_PROPERTIES = ("drainagecl", "hydgrp")

# Coverage accumulates through three weighted sums, so a complete field lands a few ulps below 1.0.
COMPLETE_COVERAGE = 0.9995

CODE_VERSION = "ds2-indicators-2026-11-15.1"


@dataclass(frozen=True)
class FieldInputs:
    field_id: str
    daily: pd.DataFrame
    latitude: float
    longitude: float
    elevation_m: float
    map_units: pd.DataFrame
    components: pd.DataFrame
    horizons: pd.DataFrame


def seasons(first: int = FIRST_SEASON, last: int = LAST_SEASON) -> list[c.Window]:
    return [
        (dt.date(year, *SEASON_START), dt.date(year, *SEASON_END))
        for year in range(first, last + 1)
    ]


def power_frame(document: dict) -> tuple[pd.DataFrame, float, float, float]:
    """Tidy a POWER daily-point response into the frame the climate indicators expect."""
    parameters = document["properties"]["parameter"]
    longitude, latitude, elevation = document["geometry"]["coordinates"]
    frame = pd.DataFrame({name: pd.Series(series) for name, series in parameters.items()})
    frame.index = [
        dt.date(int(key[:4]), int(key[4:6]), int(key[6:])) for key in frame.index
    ]
    fill = document.get("header", {}).get("fill_value", -999.0)
    # The DE converts fill values during cleaning; this is a second line of defence, because a -999
    # temperature that reached an indicator would produce a plausible wrong number rather than an error.
    frame = frame.mask(frame == fill)
    return frame.reset_index(names=c.DATE_COLUMN), latitude, longitude, elevation


def soil_tables(
    field_id: str,
    step_a: list[list],
    step_b: list[list],
    step_c: list[list],
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Build the three soil frames, computing area shares from the intersection geometry."""
    polygons = pd.DataFrame(step_a[1:], columns=step_a[0])
    components = pd.DataFrame(step_b[1:], columns=step_b[0])
    horizons = pd.DataFrame(step_c[1:], columns=step_c[0])

    to_equal_area = Transformer.from_crs("EPSG:4326", AREA_CRS, always_xy=True).transform
    def reproject(coordinates: np.ndarray) -> np.ndarray:
        return np.column_stack(to_equal_area(coordinates[:, 0], coordinates[:, 1]))

    polygons["area_m2"] = [
        shapely.transform(wkt.loads(geometry), reproject).area
        for geometry in polygons["isect_wkt"]
    ]
    areas = polygons.groupby("mukey", as_index=False)["area_m2"].sum()
    total = areas["area_m2"].sum()
    areas["area_share"] = areas["area_m2"] / total if total else None
    areas["field_id"] = field_id

    for column in ("comppct_r", "slope_r", "tfact"):
        if column in components:
            components[column] = pd.to_numeric(components[column], errors="coerce")
    for column in horizons.columns:
        if column not in ("cokey", "chkey", "hzname", "kffact"):
            horizons[column] = pd.to_numeric(horizons[column], errors="coerce")

    return areas[["field_id", "mukey", "area_share", "area_m2"]], components, horizons


def _status(value: c.IndicatorValue | s.SoilProperty, complete: bool) -> str:
    if getattr(value, "status", "") != "ok":
        return "unknown"
    return "available" if complete else "partial"


def _indicator_row(
    field_id: str,
    indicator: c.IndicatorValue,
    category: str,
    run_id: str,
) -> dict:
    complete = indicator.days_valid == indicator.days_expected
    return {
        "field_id": field_id,
        "indicator_id": indicator.indicator_id,
        "category": category,
        "value": indicator.value,
        "unit": indicator.unit,
        "status": _status(indicator, complete),
        "window_start": indicator.window_start.isoformat(),
        "window_end": indicator.window_end.isoformat(),
        "valid_obs": indicator.days_valid,
        "unknown_reason": indicator.reason,
        "run_id": run_id,
    }


def climate_rows(inputs: FieldInputs, windows: list[c.Window], run_id: str) -> list[dict]:
    """One row per field, indicator and season."""
    rows = []
    for window in windows:
        computed = [
            c.growing_degree_days(inputs.daily, window),
            c.heat_days(inputs.daily, window),
            c.seasonal_precipitation_total(inputs.daily, window),
            c.seasonal_mean_temperature(inputs.daily, window),
            c.longest_dry_spell(inputs.daily, window),
            c.dry_spell_count(inputs.daily, window),
            c.reference_et_total(
                inputs.daily, window, inputs.latitude, inputs.elevation_m
            ),
        ]
        rows.extend(_indicator_row(inputs.field_id, value, "climate", run_id) for value in computed)

        year = window[0].year
        frost = c.frost_window(inputs.daily, (dt.date(year, 1, 1), dt.date(year, 12, 31)))
        rows.append(
            {
                "field_id": inputs.field_id,
                "indicator_id": "frost_free_days",
                "category": "climate",
                "value": float(frost.frost_free_days) if frost.frost_free_days is not None else None,
                "unit": "days",
                "status": "available" if frost.status == "ok" else "unknown",
                "window_start": frost.window_start.isoformat(),
                "window_end": frost.window_end.isoformat(),
                "valid_obs": frost.days_valid,
                "unknown_reason": frost.reason,
                "run_id": run_id,
            }
        )
    return rows


def soil_rows(inputs: FieldInputs, run_id: str) -> tuple[list[dict], list[dict]]:
    """Field-level soil indicators, and the per-map-unit composition behind them."""
    indicators = []
    for column, depth in SOIL_DEPTH_PROPERTIES:
        value = s.aggregate_horizon_property(
            inputs.map_units, inputs.components, inputs.horizons, inputs.field_id, column, depth
        )
        indicators.append(_soil_indicator_row(inputs.field_id, value, run_id))

    storage = s.aggregate_available_water_storage(
        inputs.map_units, inputs.components, inputs.horizons, inputs.field_id
    )
    indicators.append(_soil_indicator_row(inputs.field_id, storage, run_id))
    slope = s.aggregate_component_property(
        inputs.map_units, inputs.components, inputs.field_id, "slope_r"
    )
    indicators.append(_soil_indicator_row(inputs.field_id, slope, run_id))

    composition = []
    names = inputs.components.drop_duplicates("mukey").set_index("mukey")["muname"]
    for _, unit in inputs.map_units.iterrows():
        share = unit["area_share"]
        composition.append(
            {
                "field_id": inputs.field_id,
                "mukey": unit["mukey"],
                "mu_name": names.get(unit["mukey"], ""),
                "share_pct": None if share is None or pd.isna(share) else round(share * 100, 4),
                "property": "map_unit_share",
                "value_num": None if share is None or pd.isna(share) else round(share * 100, 4),
                "value_text": None,
                "unit": "% of field area",
                "indicator_id": "map_unit_share",
                "run_id": run_id,
            }
        )

    for column in SOIL_CLASS_PROPERTIES:
        shares = s.aggregate_component_class(
            inputs.map_units, inputs.components, inputs.field_id, column
        )
        for label, share in sorted(shares.shares.items(), key=lambda item: -item[1]):
            composition.append(
                {
                    "field_id": inputs.field_id,
                    "mukey": "",
                    "mu_name": "",
                    "share_pct": round(share * 100, 4),
                    "property": column,
                    "value_num": round(share * 100, 4),
                    "value_text": label,
                    "unit": "% of field area",
                    "indicator_id": column,
                    "run_id": run_id,
                }
            )
        indicators.append(
            {
                "field_id": inputs.field_id,
                "indicator_id": f"{column}_dominant",
                "category": "soil",
                "value": None if shares.dominant_share is None else round(shares.dominant_share * 100, 4),
                "unit": "% of field area",
                # No majority is not missing data: the shares are known, there simply is no dominant
                # class. That is `not_assessed`, not `unknown`.
                "status": (
                    "unknown"
                    if shares.status != "ok"
                    else "available"
                    if shares.dominant is not None
                    else "not_assessed"
                ),
                "window_start": None,
                "window_end": None,
                "valid_obs": shares.map_units,
                # The dominant class is only meaningful alongside its share, so the label travels with it.
                "unknown_reason": shares.reason or f"dominant class: {shares.dominant}",
                "run_id": run_id,
            }
        )
    return indicators, composition


def _soil_indicator_row(field_id: str, value: s.SoilProperty, run_id: str) -> dict:
    complete = value.status == "ok" and value.area_coverage >= COMPLETE_COVERAGE and (
        value.depth_coverage is None or value.depth_coverage >= COMPLETE_COVERAGE
    )
    reason = value.reason
    if reason is None and not complete:
        # A partial value must say what it is partial over, or the UI can only show a bare number.
        depth = "" if value.depth_coverage is None else f", depth {value.depth_coverage:.2%}"
        reason = f"computed over {value.area_coverage:.2%} of the field's mapped area{depth}"
    return {
        "field_id": field_id,
        "indicator_id": value.property_id,
        "category": "soil",
        "value": value.value,
        "unit": value.unit,
        "status": _status(value, complete),
        "window_start": None,
        "window_end": None,
        "valid_obs": value.map_units,
        "unknown_reason": reason,
        "run_id": run_id,
    }


_SCALE = {"model_reanalysis": "grid", "survey": "field"}


def lineage_rows(run_id: str, used_indicator_ids: set[str] | None = None) -> list[dict]:
    """Lineage for exactly the indicators this run wrote, in both tables.

    The load refuses an indicator without a lineage row, so a missing record is raised here rather than
    discovered at load time. Records the modules carry for indicators this run did not emit are left out,
    so the file never ships rows that point at nothing.
    """
    records = {
        record["indicator_id"]: record
        for record in list(c.INDICATOR_LINEAGE) + list(s.SOIL_PROPERTY_LINEAGE)
    }
    # No argument means every record both modules carry, which is what a contract test wants.
    used_indicator_ids = set(records) if used_indicator_ids is None else used_indicator_ids
    missing = sorted(used_indicator_ids - set(records))
    if missing:
        raise RuntimeError(
            "no lineage record for indicator(s): "
            + ", ".join(missing)
            + ". Add them to INDICATOR_LINEAGE or SOIL_PROPERTY_LINEAGE before loading."
        )

    rows = []
    for indicator_id in sorted(used_indicator_ids):
        record = records[indicator_id]
        evidence = record["evidence_type"]
        rows.append(
            {
                "indicator_id": record["indicator_id"],
                "label": record["indicator_id"].replace("_", " "),
                "source_ids": json.dumps([record["source"]]),
                "variables": json.dumps(record["variables"]),
                "formula": record["formula"],
                "aggregation_window": record["temporal_window"],
                "spatial_support": record["spatial_scale"],
                "scale": _SCALE[evidence],
                "resolution": record["spatial_scale"],
                "evidence_type": evidence,
                "missing_data_rule": record["missing_data_rule"],
                "interpretation": record["formula"],
                "limitation": record["limitation"],
                "code_version": CODE_VERSION,
                "run_id": run_id,
            }
        )
    return rows


def marsden_gdd_reference(daily: pd.DataFrame, windows: list[c.Window]) -> float | None:
    """Mean growing-degree-day total at the Marsden site, the baseline the applicability rule compares to."""
    values = [c.growing_degree_days(daily, window) for window in windows]
    usable = [value.value for value in values if value.value is not None]
    return sum(usable) / len(usable) if usable else None


def climate_distance_row(
    field_id: str,
    field_rows: list[dict],
    reference: float | None,
    windows: list[c.Window],
    run_id: str,
) -> dict:
    gdd = [row["value"] for row in field_rows if row["indicator_id"] == "gdd" and row["value"] is not None]
    value = None
    reason = None
    if reference is None:
        reason = "no Marsden-site reference available"
    elif not gdd:
        reason = "no usable growing-degree-day season for this field"
    else:
        value = abs(sum(gdd) / len(gdd) - reference)
    return {
        "field_id": field_id,
        "indicator_id": "gdd_season_difference_vs_marsden",
        "category": "climate",
        "value": value,
        "unit": "degree-days C",
        "status": "available" if value is not None else "unknown",
        "window_start": windows[0][0].isoformat(),
        "window_end": windows[-1][1].isoformat(),
        "valid_obs": len(gdd),
        "unknown_reason": reason,
        "run_id": run_id,
    }


class RawStore:
    """Reads the raw objects, from S3 or from a local copy of the same layout."""

    def __init__(self, local: Path | None = None):
        self.local = local
        self.client = None
        self.bucket = None
        if local is None:
            import boto3
            from dotenv import load_dotenv

            load_dotenv(REPO_ROOT / ".env")
            import os

            self.client = boto3.client(
                "s3",
                region_name=os.environ["AWS_REGION"],
                aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
                aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
            )
            self.bucket = os.environ["S3_BUCKET"]

    def read_json(self, key: str) -> dict:
        if self.local is not None:
            return json.loads((self.local / key).read_text(encoding="utf-8"))
        return json.loads(self.client.get_object(Bucket=self.bucket, Key=key)["Body"].read())

    def power(self, point_id: str) -> dict:
        return self.read_json(f"{POWER_PREFIX}/{point_id}{POWER_SUFFIX}")

    def ssurgo(self, field_id: str, step: str) -> list[list]:
        return self.read_json(f"{SSURGO_PREFIX}/{field_id}/{step}.json")["Table"]


def field_ids(path: Path = FIELDS_PATH) -> list[str]:
    document = json.loads(path.read_text(encoding="utf-8"))
    return [feature["properties"]["field_id"] for feature in document["features"]]


def load_field(store: RawStore, field_id: str) -> FieldInputs:
    daily, latitude, longitude, elevation = power_frame(store.power(field_id))
    map_units, components, horizons = soil_tables(
        field_id,
        store.ssurgo(field_id, "step_a_map_units"),
        store.ssurgo(field_id, "step_b_components"),
        store.ssurgo(field_id, "step_c_horizons"),
    )
    return FieldInputs(
        field_id=field_id,
        daily=daily,
        latitude=latitude,
        longitude=longitude,
        elevation_m=elevation,
        map_units=map_units,
        components=components,
        horizons=horizons,
    )


def run(
    store: RawStore,
    fields: list[str],
    out: Path = DEFAULT_OUT,
    windows: list[c.Window] | None = None,
    run_id: str | None = None,
) -> dict:
    windows = windows or seasons()
    run_id = run_id or f"ds2-indicators-{uuid.uuid4().hex[:12]}"

    marsden_daily, _, _, _ = power_frame(store.power(MARSDEN_POINT))
    reference = marsden_gdd_reference(marsden_daily, windows)

    indicators: list[dict] = []
    composition: list[dict] = []
    soil_findings: dict[str, list[str]] = {}

    for field_id in fields:
        inputs = load_field(store, field_id)
        findings = s.check_soil_tables(inputs.map_units, inputs.components, inputs.horizons)
        if findings:
            soil_findings[field_id] = findings

        field_rows = climate_rows(inputs, windows, run_id)
        field_rows.append(climate_distance_row(field_id, field_rows, reference, windows, run_id))
        soil_indicators, field_composition = soil_rows(inputs, run_id)

        indicators.extend(field_rows + soil_indicators)
        composition.extend(field_composition)

    out.mkdir(parents=True, exist_ok=True)
    indicator_frame = pd.DataFrame(indicators)
    composition_frame = pd.DataFrame(composition)
    used = set(indicator_frame["indicator_id"]) | set(composition_frame["indicator_id"])
    lineage_frame = pd.DataFrame(lineage_rows(run_id, used))
    indicator_frame.to_csv(out / "field_indicators.csv", index=False)
    composition_frame.to_csv(out / "soil_properties.csv", index=False)
    lineage_frame.to_csv(out / "indicator_lineage.csv", index=False)

    manifest = {
        "run_id": run_id,
        "code_version": CODE_VERSION,
        "generated_utc": dt.datetime.now(dt.UTC).isoformat(timespec="seconds"),
        "fields": len(fields),
        "seasons": [f"{window[0]} to {window[1]}" for window in windows],
        "marsden_gdd_reference": reference,
        "rows": {
            "field_indicators": len(indicator_frame),
            "soil_properties": len(composition_frame),
            "indicator_lineage": len(lineage_frame),
        },
        "soil_table_findings": soil_findings,
    }
    (out / "run_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return {
        "indicators": indicator_frame,
        "composition": composition_frame,
        "lineage": lineage_frame,
        "manifest": manifest,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fields", nargs="*", help="field ids; default is every field")
    parser.add_argument("--local", type=Path, help="read raw/ from this directory instead of S3")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--first-season", type=int, default=FIRST_SEASON)
    parser.add_argument("--last-season", type=int, default=LAST_SEASON)
    args = parser.parse_args(argv)

    store = RawStore(local=args.local)
    fields = args.fields or field_ids()
    result = run(
        store, fields, out=args.out, windows=seasons(args.first_season, args.last_season)
    )
    manifest = result["manifest"]

    print(f"run {manifest['run_id']} over {manifest['fields']} field(s)")
    for table, count in manifest["rows"].items():
        print(f"  {table:<22}{count:>8} rows")
    statuses = result["indicators"]["status"].value_counts().to_dict()
    print("  status:", ", ".join(f"{name} {count}" for name, count in sorted(statuses.items())))
    if manifest["soil_table_findings"]:
        print(f"  soil table findings on {len(manifest['soil_table_findings'])} field(s):")
        for field_id, findings in manifest["soil_table_findings"].items():
            for finding in findings:
                print(f"    {field_id}: {finding}")
    print(f"  written to {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
