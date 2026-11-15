"""Backward-compatibility shim — re-exports everything from api.db.facts."""
from __future__ import annotations

from api.db.facts import (  # noqa: F401
    FIRST_CROP_YEAR,
    FieldRecord,
    IndicatorFacts,
    SeasonalMean,
    SoilMeasure,
)
