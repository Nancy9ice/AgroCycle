"""Provenance for weather indicators, read from DS2's lineage records rather than retyped.

`transform.indicators.climate.INDICATOR_LINEAGE` states each indicator's source, grid scale, missing-data
rule, limitation and evidence type. The profile screen's provenance drawer shows the same facts, so they come
from the one place that owns them. Imported on first use: that module needs pandas, which the project
already depends on, and a missing install should fail the request clearly, not the whole server at start.
"""
from __future__ import annotations

from functools import cache
from typing import Any


@cache
def lineage_by_indicator() -> dict[str, dict[str, Any]]:
    from transform.indicators.climate import INDICATOR_LINEAGE

    return {record["indicator_id"]: record for record in INDICATOR_LINEAGE}


def lineage_for(indicator_id: str) -> dict[str, Any]:
    """The lineage record, or a loud error: a profile must not show an indicator nobody documented."""
    try:
        return lineage_by_indicator()[indicator_id]
    except KeyError:
        raise LookupError(f"no lineage record for indicator {indicator_id!r}") from None


def thresholds() -> dict[str, float]:
    """The thresholds the indicators actually use, so plain-language text never drifts from the code."""
    from transform.indicators import climate

    return {
        "heat_day_c": climate.HEAT_DAY_THRESHOLD_C,
        "gdd_base_c": climate.GDD_BASE_C,
        "gdd_cap_c": climate.GDD_UPPER_CAP_C,
        "dry_spell_min_days": climate.DRY_SPELL_MIN_DAYS,
        "wet_day_mm": climate.WET_DAY_THRESHOLD_MM,
    }
