"""Backward-compatibility shim — re-exports everything from api.core.crop_summary."""
from __future__ import annotations

from api.core.crop_summary import (  # noqa: F401
    CROP_LABELS,
    MAX_REPEATS_FOR_ALTERNATING,
    describe_sequence,
)
