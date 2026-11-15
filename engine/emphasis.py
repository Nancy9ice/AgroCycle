"""Order the comparison by what the farmer said matters (AgroCycle, DS2, roadmap Phase 10).

PRD 8.5 says a strategy may be attractive for one objective and unsuitable for another, so the comparison
should be shaped by the farmer's priorities. The same section forbids a composite score without explicit
components, weights and sensitivity. Both hold at once if priorities change **what is shown first and what
is called out**, and never the outcome, the strategies' feasibility or any ranking between them.

So this module reorders and annotates. It cannot change a decision: it takes a finished `Decision` and
returns the same outcomes in a different order, plus the gaps worth naming for the priorities chosen. Every
outcome is still returned, including the ones that cannot be claimed, because hiding an outcome because a
farmer did not ask about it is how a comparison becomes a sales pitch.

A priority the farmer rated `low` is not the same as one they did not mention: the first is an answer, the
second is silence, and neither promotes anything.
"""
from __future__ import annotations

from dataclasses import dataclass

from engine.decision import Decision, OutcomeAssessment

HIGH = "high"
MEDIUM = "medium"

# Which evidence speaks to which priority. An outcome can serve more than one.
PRIORITY_OUTCOMES: dict[str, tuple[str, ...]] = {
    "soil": ("soil_carbon_change", "erosion_reduction", "applied_n_reduction"),
    "water": ("nitrate_leaching_reduction", "applied_n_reduction"),
    "inputs": ("applied_n_reduction", "herbicide_reduction"),
    "income": ("profitability_parity", "yield_parity"),
    "forage": ("forage_supply",),
}

# What we cannot answer for each priority, said in the farmer's terms rather than ours.
PRIORITY_GAPS: dict[str, str] = {
    "soil": (
        "Nothing here measures soil carbon or erosion on your field, so the soil-health question is "
        "answered only by how much less nitrogen and herbicide the longer rotations needed at one "
        "research farm."
    ),
    "water": (
        "Nothing here measures water leaving your soil. Rainfall and dry spells come from a weather grid "
        "about 50 km across, and applying less nitrogen is not the same as measuring less nitrate."
    ),
    "inputs": (
        "The input figures are the strongest evidence we have, but they are one research farm over nine "
        "seasons, and most of the diversified systems' nitrogen came from manure."
    ),
    "income": (
        "AgroCycle does not work out profit. The researchers found no significant difference in net "
        "returns at their prices and costs, which is not a forecast for your farm."
    ),
    "forage": (
        "We have no figures for forage yield, quality or feed value. That the four-year rotation grows "
        "alfalfa for two years is part of how it is defined, not a measured amount of feed."
    ),
}


@dataclass(frozen=True)
class EmphasisedComparison:
    """The same decision, ordered for one farmer. Nothing here changes what the engine concluded."""

    outcome: str
    outcome_reason: str
    outcomes: tuple[OutcomeAssessment, ...]
    highlighted: tuple[str, ...]
    gaps_for_priorities: tuple[str, ...]
    priorities_used: tuple[str, ...]
    note: str = (
        "Your priorities decide what is shown first and which gaps are called out. They do not change the "
        "result, and no option is scored or ranked against another."
    )


def _chosen(priorities: dict[str, str] | None) -> tuple[str, ...]:
    if not priorities:
        return ()
    return tuple(
        key
        for key, level in priorities.items()
        if key in PRIORITY_OUTCOMES and str(level).lower() in (HIGH, MEDIUM)
    )


def emphasise(decision: Decision, priorities: dict[str, str] | None = None) -> EmphasisedComparison:
    """Reorder a finished decision for the priorities given. The decision itself is untouched."""
    chosen = _chosen(priorities)
    wanted: list[str] = []
    for key in chosen:
        for outcome_id in PRIORITY_OUTCOMES[key]:
            if outcome_id not in wanted:
                wanted.append(outcome_id)

    by_id = {outcome.outcome_id: outcome for outcome in decision.outcomes}
    highlighted = tuple(outcome_id for outcome_id in wanted if outcome_id in by_id)
    # Stable: highlighted ones first in priority order, then everything else in the engine's order.
    ordered = [by_id[outcome_id] for outcome_id in highlighted]
    ordered += [outcome for outcome in decision.outcomes if outcome.outcome_id not in highlighted]

    return EmphasisedComparison(
        outcome=decision.outcome,
        outcome_reason=decision.outcome_reason,
        outcomes=tuple(ordered),
        highlighted=highlighted,
        gaps_for_priorities=tuple(PRIORITY_GAPS[key] for key in chosen),
        priorities_used=chosen,
    )
