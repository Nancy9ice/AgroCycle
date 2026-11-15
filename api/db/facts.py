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
    # From DE's field notes (a mapped soil unit at the field centre). None if not loaded.
    soil_series: str | None = None
    soil_map_unit: str | None = None


@dataclass(frozen=True)
class SeasonalMean:
    """One weather indicator averaged over the seasons whose result was `available`.

    A season that was `partial` or `unknown` is not in the mean, and `seasons_total` says how many
    there were, so a thin result can never pass as a full one.
    """

    indicator_id: str
    mean: float
    unit: str
    seasons_used: int
    seasons_total: int
    first_year: int
    last_year: int
    # Month numbers of the first season's window, e.g. 4 and 11 for April to November.
    start_month: int
    end_month: int


@dataclass(frozen=True)
class SoilMeasure:
    """One area-weighted soil survey value for a field (top 30 cm, or top 100 cm for water storage)."""

    indicator_id: str
    value: float
    unit: str
    # DS2's own words when the value covers only part of the field, e.g. "computed over 96.72% of ...".
    # Empty when the value is complete. A partial value is shown, with this note, never silently.
    coverage_note: str = ""


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
    # Weather indicators the profile screen shows, by runner indicator id.
    seasonal: dict[str, SeasonalMean] = field(default_factory=dict)
    # Soil survey measures the profile screen shows, by runner indicator id.
    soil: dict[str, SoilMeasure] = field(default_factory=dict)
    # Drainage classes with their share of the field's mapped area, largest first. A field is rarely one
    # class; the screen shows the mix, not just the biggest part.
    drainage_shares: tuple[tuple[str, float], ...] = ()
