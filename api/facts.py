"""Plain data the API reads about a field, independent of where it is stored."""
from __future__ import annotations

from dataclasses import dataclass, field

# The engine's four required indicators (`engine.decision.REQUIRED_INDICATORS`).
FIRST_CROP_YEAR = 2015


@dataclass(frozen=True)
class FieldRecord:
    field_id: str
    county: str
    boundary_source: str  # "demo" | "real"
    role: str  # "primary" | "test"
    # DE's class: "rotation", "continuous_corn", "pasture_hay", "mixed" or "other"; None if not loaded.
    field_class: str | None
    # One letter per year from FIRST_CROP_YEAR, e.g. "SCSCSCSCSCS"; None if not loaded.
    crop_sequence: str | None


@dataclass(frozen=True)
class IndicatorFacts:
    """What the indicator pipeline produced for one field, reduced to what the engine reads.

    Every field defaults to "nothing known", so an absent pipeline output is unknown, never a value.
    """

    gdd_season_difference_vs_marsden: float | None = None
    frost_free_days: int | None = None
    dominant_drainage_class: str | None = None
    # Engine indicator id -> "ok" | "unknown" (see `profile.py` for the mapping and its rule).
    statuses: dict[str, str] = field(default_factory=dict)
