"""Backward-compatibility shim — re-exports everything from api.core.lineage."""
from __future__ import annotations

from api.core.lineage import (  # noqa: F401
    lineage_by_indicator,
    lineage_for,
    thresholds,
)
