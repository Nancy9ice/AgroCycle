"""Backward-compatibility shim — re-exports everything from api.core.profile."""
from __future__ import annotations

from api.core.profile import (  # noqa: F401
    NO_HISTORY,
    RUNNER_TO_ENGINE_INDICATOR,
    SAMPLE_FROST_FREE_DAYS,
    SAMPLE_GDD_DIFFERENCE,
    build_profile,
    crop_history_summary,
    indicator_statuses,
)
