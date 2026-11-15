"""Builds the engine's `FieldProfile` from stored facts. All mapping decisions live here, in one place.

Two modules written by the same team disagree on names and statuses, and this is where they are
reconciled, conservatively:

* DS2's runner (`transform/indicators/runner.py`) writes ``frost_free_days``; the engine requires
  ``frost_window``. They are the same measurement, so one is mapped to the other.
* The runner marks a season ``available``, ``partial`` or ``unknown``; the engine wants ``ok`` or not.
  A required indicator is ``ok`` only if *every* season row for it is ``available``. A ``partial`` row
  (computed from fewer days than the window holds) counts as ``unknown``, and so does a missing one.
  DS2 can relax this with a written reason; relaxing it silently would read thin data as complete.
"""
from __future__ import annotations

from collections.abc import Iterable, Mapping

from api.core.crop_summary import describe_sequence
from api.db.facts import FIRST_CROP_YEAR, FieldRecord, IndicatorFacts
from engine import decision as engine

# Runner indicator id -> the id the engine requires.
RUNNER_TO_ENGINE_INDICATOR = {
    "gdd": "gdd",
    "precipitation_total": "precipitation_total",
    "frost_free_days": "frost_window",
    "om_r_0_30cm": "om_r_0_30cm",
}

# Demo affordance only: the values behind `sample_indicators`. Not any field's data.
SAMPLE_GDD_DIFFERENCE = 120.0
SAMPLE_FROST_FREE_DAYS = 150

NO_HISTORY = "Crop history is not loaded for this field."


def indicator_statuses(rows: Iterable[Mapping[str, str]]) -> dict[str, str]:
    """Collapse per-season runner rows into the engine's one status per required indicator."""
    seen: dict[str, list[bool]] = {}
    for row in rows:
        engine_id = RUNNER_TO_ENGINE_INDICATOR.get(row["indicator_id"])
        if engine_id is not None:
            seen.setdefault(engine_id, []).append(row["status"] == "available")
    return {
        engine_id: "ok" if all(flags) else "unknown" for engine_id, flags in seen.items()
    }


def crop_history_summary(record: FieldRecord) -> str:
    if not record.crop_sequence:
        return NO_HISTORY
    return describe_sequence(record.crop_sequence, FIRST_CROP_YEAR)


def build_profile(
    record: FieldRecord, indicators: IndicatorFacts, *, sample_indicators: bool = False
) -> engine.FieldProfile:
    """The engine's view of one field. Anything not established is left as `UNKNOWN`."""
    # DE's `rotation` class is the one in-domain class; a field with no class is unknown, not "no".
    is_rotation = None if record.field_class is None else record.field_class == "rotation"

    if sample_indicators:
        statuses = {indicator: "ok" for indicator in engine.REQUIRED_INDICATORS}
        gdd_difference: float | None = SAMPLE_GDD_DIFFERENCE
        frost_free_days: int | None = SAMPLE_FROST_FREE_DAYS
    else:
        statuses = dict(indicators.statuses)
        gdd_difference = indicators.gdd_season_difference_vs_marsden
        frost_free_days = indicators.frost_free_days

    return engine.FieldProfile(
        field_id=record.field_id,
        boundary_source=record.boundary_source,
        crop_history_summary=crop_history_summary(record),
        county=record.county,
        crop_history_is_maize_soybean=is_rotation,
        gdd_season_difference_vs_marsden=gdd_difference,
        frost_free_days=frost_free_days,
        dominant_drainage_class=indicators.dominant_drainage_class,
        indicator_statuses=statuses,
    )
