"""Build the season stress summary from a field's indicator rows. Pure: no I/O.

This is a count of past weather per whole season, not a crop-phase stress test: nothing here says when in the
season a hot or dry spell happened, because the experiment's records give no planting or growth-stage timing.
"""
from __future__ import annotations

import math

from api.core.lineage import lineage_for, thresholds
from api.schemas.season import (
    SeasonExtremeOut,
    SeasonIndicatorOut,
    SeasonSummaryOut,
    SeasonThresholdOut,
    SeasonValueOut,
)

# In the order a reader meets them: heat, dryness, rain, warmth.
INDICATORS = (
    "heat_days",
    "longest_dry_spell",
    "dry_spell_count",
    "precipitation_total",
    "gdd",
    "mean_temperature",
    "reference_et_total",
)


def _label(indicator_id: str) -> str:
    t = thresholds()
    return {
        "heat_days": f"Very hot days ({t['heat_day_c']:g} °C or more)",
        "longest_dry_spell": f"Longest run of days with under {t['wet_day_mm']:g} mm of rain",
        "dry_spell_count": f"Dry spells of {t['dry_spell_min_days']:g} or more days",
        "precipitation_total": "Rain over the season",
        "gdd": "Warmth for crop growth (growing degree days)",
        "mean_temperature": "Average temperature over the season",
        "reference_et_total": "Reference evapotranspiration (grass-surface demand, not any crop's water use)",
    }[indicator_id]


def _number(text: object) -> float | None:
    try:
        value = float(text)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    return None if math.isnan(value) else round(value, 2)  # NaN is unknown; two decimals hides float noise


def _extreme(known: list[SeasonValueOut], pick) -> SeasonExtremeOut | None:
    """The season with the largest or smallest value; `max` and `min` keep the first of equal values, the earliest."""
    if not known:
        return None
    season = pick(known, key=lambda s: s.value)
    return SeasonExtremeOut(year=season.year, value=season.value)


def _caveats(thresholds_table: dict[str, dict] | None = None) -> list[str]:
    t = thresholds()
    reviewed = bool(thresholds_table) and all(r["review"] == "expert_reviewed" for r in thresholds_table.values())
    return [
        (
            "These are counts of past weather in a weather-model grid cell about 50 km across, not measurements at "
            "this field, and not a prediction of yield or loss. Two fields in the same cell share the same numbers."
        ),
        (
            f"The thresholds ({t['heat_day_c']:g} °C, a dry spell of {t['dry_spell_min_days']:g} days) are the "
            "team's own defaults. "
            + ("An agronomist has reviewed them." if reviewed else "No agronomist has reviewed them.")
        ),
        (
            "Each figure covers a whole season. It says nothing about when in the season the hot or dry days fell, "
            "so it cannot say whether a crop was at a sensitive stage."
        ),
        (
            "NASA POWER rainfall ran about 11 % lower than the Marsden Farm station record in 2003 to 2011, so dry "
            "spells computed from it are more likely overstated than understated."
        ),
    ]


def build_season_summary(
    field_id: str, rows: list[dict], data_version: str, thresholds_table: dict[str, dict] | None = None
) -> SeasonSummaryOut:
    indicators: list[SeasonIndicatorOut] = []
    for indicator_id in INDICATORS:
        mine = [r for r in rows if r["indicator_id"] == indicator_id and len(str(r["window_end"])) >= 4]
        if not mine:
            continue
        seasons = sorted(
            (
                SeasonValueOut(
                    year=int(str(r["window_end"])[:4]),
                    value=_number(r["value"]) if r["status"] != "unknown" else None,
                    status=str(r["status"]),
                    window_start=str(r["window_start"]),
                    window_end=str(r["window_end"]),
                    unknown_reason=str(r.get("unknown_reason") or ""),
                )
                for r in mine
            ),
            key=lambda s: s.year,
        )
        known = [s for s in seasons if s.value is not None]
        lineage = lineage_for(indicator_id)
        indicators.append(
            SeasonIndicatorOut(
                indicator_id=indicator_id,
                label=_label(indicator_id),
                unit=lineage["unit"],
                evidence_type=lineage["evidence_type"],
                scale="grid",
                source=lineage["source"],
                formula=lineage["formula"],
                limitation=lineage["limitation"],
                threshold=(
                    SeasonThresholdOut(**thresholds_table[indicator_id])
                    if thresholds_table and indicator_id in thresholds_table
                    else None
                ),
                seasons=seasons,
                seasons_used=len(known),
                seasons_total=len(seasons),
                # min/max keep the first of equal values, which is the earliest season.
                highest=_extreme(known, max),
                lowest=_extreme(known, min),
            )
        )
    years = [s.year for i in indicators for s in i.seasons]
    return SeasonSummaryOut(
        field_id=field_id,
        period=f"{min(years)}-{max(years)}" if years else "not loaded",
        indicators=indicators,
        caveats=_caveats(thresholds_table) if indicators else ["No weather indicators have been loaded for this field."],
        data_version=data_version,
    )
