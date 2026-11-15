"""Build the transition sequence for switching to strategy B or C from DS2's rows. Pure: no I/O.

DS2 found no source in the Marsden paper or its supplement for planting dates, phase windows or establishment
guidance. The only timing fact is that composted manure went on in October. So this shows the sequence the
experiment establishes, the needs DS2 derived from the rotation definition (marked as the team's own), and "not
established" wherever timing is not sourced. It adds nothing of its own.
"""
from __future__ import annotations

import json

from api.schemas.transition import ReadinessOut, TransitionOut, TransitionStepOut
from engine.rules.strategy_rules import STRATEGY_PROFILES

NOT_ESTABLISHED_PREFIX = "not established"
SWITCHABLE = ("B", "C")

CAVEATS = [
    "One way to switch, as a starting point for your adviser, not a final plan.",
    (
        "The sequence comes from the rotations in the Marsden Farm experiment. The experiment's papers give no "
        "planting dates, no windows and no establishment advice, so none are shown. Where a step says timing is "
        "not established, that is the honest answer, not a gap to fill with a guess."
    ),
    (
        "The only timing the sources give is the manure: composted manure was applied in October. Without manure "
        "the nitrogen saving in the comparison does not apply."
    ),
    (
        "Needs marked as the team's own are read from how the rotation is defined. They are not from a source "
        "and no agronomist has reviewed them."
    ),
    "There is no cost, yield or profit here. AgroCycle does not work those out.",
]

# What the farmer's own answers say about each step: (constraint, label, the step it bears on, strategies it applies to).
_READINESS = (
    ("manure_access", "Access to composted manure", 0, ("B", "C")),
    ("small_grain_equipment_or_contractor", "Equipment, or a contractor, for small grain", 3, ("B", "C")),
    ("oat_use_or_buyer", "A use or buyer for oat grain and straw", 3, ("B", "C")),
    ("forage_use_or_buyer", "A use or buyer for the alfalfa forage", 4, ("C",)),
)


def _readiness(strategy_id: str, constraints: dict | None) -> list[ReadinessOut] | None:
    if constraints is None:
        return None
    out = []
    for key, label, year, applies in _READINESS:
        if strategy_id not in applies:
            continue
        answer = constraints.get(key)
        out.append(
            ReadinessOut(
                constraint=key, label=label, answer=answer,
                status="not_answered" if answer is None else "yes" if answer else "no",
                step_year=year,
            )
        )
    return out


def build_transition(
    strategy_id: str, rows: list[dict], data_version: str, constraints: dict | None = None
) -> TransitionOut | None:
    """None when DS2's table has no steps for this strategy."""
    if not rows:
        return None
    profile = next(p for p in STRATEGY_PROFILES if p.strategy_id == strategy_id)
    steps = [
        TransitionStepOut(
            year=int(r["year"]), crop=r["crop"], action=r["action"],
            needs=json.loads(r["needs"]) if isinstance(r["needs"], str) else list(r["needs"]),
            timing_note=r["timing_note"],
            timing_established=not r["timing_note"].lower().startswith(NOT_ESTABLISHED_PREFIX),
            evidence_basis=r["evidence_basis"], source=r["source"],
            shows_past_weather=bool(r["stress_phase"]),
        )
        for r in sorted(rows, key=lambda r: int(r["year"]))
    ]
    return TransitionOut(
        strategy_id=strategy_id, label=profile.label, rotation=profile.rotation,
        rules_version=rows[0]["rules_version"], steps=steps,
        readiness=_readiness(strategy_id, constraints), caveats=CAVEATS, data_version=data_version,
    )
