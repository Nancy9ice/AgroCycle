"""Turns the engine's dataclasses into JSON-safe values. `UNKNOWN` becomes `null`."""
from __future__ import annotations

import dataclasses
from collections.abc import Mapping
from typing import Any

from engine.decision import UNKNOWN


def to_plain(value: Any) -> Any:
    """Recursively convert dataclasses, tuples and mappings; the engine's sentinel becomes None."""
    if value is UNKNOWN:
        return None
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return {f.name: to_plain(getattr(value, f.name)) for f in dataclasses.fields(value)}
    if isinstance(value, Mapping):
        return {key: to_plain(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_plain(item) for item in value]
    return value
