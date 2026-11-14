import type { Decision, OutcomeAssessment } from "./types";

/**
 * Which outcomes speak to each priority from the priorities form. The engine records priorities
 * and does not act on them (DS2 decision-engine spec, criterion 10), so priorities only decide what
 * the screen points out. A priority with no outcome here says so instead of staying quiet.
 */
const outcomesByPriority: Readonly<Record<string, readonly string[]>> = {
  soil: ["soil_carbon_change", "erosion_reduction"],
  water: [],
  inputs: ["applied_n_reduction", "herbicide_reduction"],
  income: ["profitability_parity", "yield_parity"],
  forage: ["forage_supply"],
};

export const priorityLabels: Readonly<Record<string, string>> = {
  soil: "Look after the soil",
  water: "Cope better with dry or wet years",
  inputs: "Spend less on fertiliser and weed-killer",
  income: "Earn from more than two crops",
  forage: "Grow hay or feed for animals",
};

export interface PriorityReading {
  id: string;
  label: string;
  related: readonly OutcomeAssessment[];
  /** Related outcomes the engine lets us speak to. */
  speakable: readonly OutcomeAssessment[];
}

const isSpeakable = (outcome: OutcomeAssessment) =>
  outcome.status === "in_domain" || outcome.status === "qualified";

/** Reads each high priority against what the engine actually returned. */
export function readPriorities(decision: Decision): PriorityReading[] {
  return decision.priorities_recorded.map((id) => {
    const related = decision.outcomes.filter((o) =>
      (outcomesByPriority[id] ?? []).includes(o.outcome_id),
    );
    return {
      id,
      label: priorityLabels[id] ?? id,
      related,
      speakable: related.filter(isSpeakable),
    };
  });
}

/** Ids of outcomes tied to a high priority, so the outcome list can tag them. */
export function highlightedOutcomeIds(decision: Decision): ReadonlySet<string> {
  return new Set(
    decision.priorities_recorded.flatMap((id) => outcomesByPriority[id] ?? []),
  );
}
