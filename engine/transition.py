"""The transition sequence for switching to strategy B or C (AgroCycle, DS2, roadmap Phase 9; BE's F6).

What this is, and what it deliberately is not.

BE asked for a transition planner with timing notes and a "you'll need" list per crop phase. I searched the
Marsden supplement (Text S1, 13,849 characters) and the paper itself (44,417 characters) for planting dates,
phase windows, establishment guidance and cutting schedules. **There are none.** The only timing fact either
document gives is that composted manure was applied in October of each year.

So this table carries the sequence, which the experiment does establish, and says "not established" for every
timing and need the experiment does not. Writing plausible sowing dates would have been inventing agronomy,
and two applicability rules were withdrawn on 2026-11-15 for exactly that.

Every row states its own ``evidence_basis``:

* ``experimental`` — the rotation sequence and the manure timing, from Davis et al. (2012) and its supplement
* ``team_proposed`` — operational needs we derived from the rotation definition, not from a source
* ``assumption`` — nothing in this table, and nothing should be added with it without a citable source
"""
from __future__ import annotations

from dataclasses import dataclass

from engine.rules.strategy_rules import MARSDEN_PAPER, MARSDEN_SUPPLEMENT, OUR_REPRODUCTION

NOT_ESTABLISHED = "not established: no source gives timing for this phase"


@dataclass(frozen=True)
class TransitionStep:
    """One year of the switch to a longer rotation."""

    strategy_id: str
    year: int
    crop: str
    action: str
    timing_note: str
    needs: tuple[str, ...]
    stress_phase: str
    evidence_basis: str
    source: str


_SEQUENCE_SOURCE = f"Rotation definitions of the Marsden Farm experiment, {MARSDEN_PAPER}"
_MANURE_SOURCE = f"{MARSDEN_SUPPLEMENT}, Text S1; reproduced in {OUR_REPRODUCTION}"

TRANSITION_STEPS: tuple[TransitionStep, ...] = (
    TransitionStep(
        strategy_id="B",
        year=1,
        crop="corn",
        action="Grow corn, as you do now.",
        timing_note=NOT_ESTABLISHED,
        needs=("The equipment and markets you already have",),
        stress_phase="season_stress",
        evidence_basis="experimental",
        source=_SEQUENCE_SOURCE,
    ),
    TransitionStep(
        strategy_id="B",
        year=2,
        crop="soybean",
        action="Grow soybean, as you do now.",
        timing_note=NOT_ESTABLISHED,
        needs=("The equipment and markets you already have",),
        stress_phase="season_stress",
        evidence_basis="experimental",
        source=_SEQUENCE_SOURCE,
    ),
    TransitionStep(
        strategy_id="B",
        year=3,
        crop="oat with red clover",
        action=(
            "Grow oat with red clover sown underneath. This is the year that makes the rotation "
            "three years long instead of two."
        ),
        timing_note=NOT_ESTABLISHED,
        needs=(
            "Somewhere to sell or use the oat grain and straw",
            "Small-grain harvest equipment, your own or a contractor's",
            "Red clover seed and a way to sow it into the oat",
        ),
        stress_phase="season_stress",
        evidence_basis="team_proposed",
        source="Derived from the rotation definition, not from a source on how to establish it",
    ),
    TransitionStep(
        strategy_id="C",
        year=1,
        crop="corn",
        action="Grow corn, as you do now.",
        timing_note=NOT_ESTABLISHED,
        needs=("The equipment and markets you already have",),
        stress_phase="season_stress",
        evidence_basis="experimental",
        source=_SEQUENCE_SOURCE,
    ),
    TransitionStep(
        strategy_id="C",
        year=2,
        crop="soybean",
        action="Grow soybean, as you do now.",
        timing_note=NOT_ESTABLISHED,
        needs=("The equipment and markets you already have",),
        stress_phase="season_stress",
        evidence_basis="experimental",
        source=_SEQUENCE_SOURCE,
    ),
    TransitionStep(
        strategy_id="C",
        year=3,
        crop="oat with alfalfa",
        action="Grow oat with alfalfa sown underneath, which starts the two alfalfa years.",
        timing_note=NOT_ESTABLISHED,
        needs=(
            "Somewhere to sell or use the oat grain and straw",
            "Small-grain harvest equipment, your own or a contractor's",
            "Alfalfa seed and a way to sow it into the oat",
        ),
        stress_phase="season_stress",
        evidence_basis="team_proposed",
        source="Derived from the rotation definition, not from a source on how to establish it",
    ),
    TransitionStep(
        strategy_id="C",
        year=4,
        crop="alfalfa",
        action=(
            "Keep the field in alfalfa for a full year. This is the biggest commitment in the "
            "four-year rotation: a quarter of your land is out of corn and soybean for two years."
        ),
        timing_note=NOT_ESTABLISHED,
        needs=(
            "A use for the forage on your own farm, or a buyer",
            "Forage harvest equipment and somewhere to store the hay",
        ),
        stress_phase="season_stress",
        evidence_basis="team_proposed",
        source="Derived from the rotation definition, not from a source on how to manage it",
    ),
    TransitionStep(
        strategy_id="B",
        year=0,
        crop="manure",
        action=(
            "Both longer rotations at Marsden received composted manure. Without it, the nitrogen "
            "saving shown in the comparison does not apply to your field."
        ),
        timing_note="Applied in October of each year (Text S1)",
        needs=("Access to composted manure and a way to spread it",),
        stress_phase="",
        evidence_basis="experimental",
        source=_MANURE_SOURCE,
    ),
    TransitionStep(
        strategy_id="C",
        year=0,
        crop="manure",
        action=(
            "Both longer rotations at Marsden received composted manure. Without it, the nitrogen "
            "saving shown in the comparison does not apply to your field."
        ),
        timing_note="Applied in October of each year (Text S1)",
        needs=("Access to composted manure and a way to spread it",),
        stress_phase="",
        evidence_basis="experimental",
        source=_MANURE_SOURCE,
    ),
)

EVIDENCE_BASES = ("experimental", "team_proposed", "assumption")
