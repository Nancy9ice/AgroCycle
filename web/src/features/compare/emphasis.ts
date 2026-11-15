import type { Answers } from "@/features/priorities/questions";
import { priorityLabels } from "./priority-links";
import type { Decision, OutcomeAssessment } from "./types";

/**
 * The comparison ordered for one farmer's priorities, as the API returns it (DS2's `engine.emphasis`). It reorders
 * and annotates a finished decision and never changes it: there is no score, rank, winner or weight in it.
 */
export interface Emphasis {
  /** Every outcome id, priority ones first. Nothing is hidden. */
  outcome_order: string[];
  /** The outcome ids promoted, in priority order. */
  highlighted: string[];
  /** Plain words for what we cannot answer, one per priority used, in the order of `priorities_used`. */
  gaps_for_priorities: string[];
  priorities_used: string[];
  note: string;
}

export type PriorityLevel = "low" | "medium" | "high";

const PRIORITY_IDS = ["soil", "water", "inputs", "income", "forage"] as const;
const LEVELS: readonly string[] = ["low", "medium", "high"];

/**
 * The farmer's answer for each priority they answered, straight from the form. An unanswered priority is left
 * out: silence is not the same as "low", and the API treats them differently from a "low" it was told.
 */
export function toPriorityLevels(
  answers: Answers,
): Partial<Record<string, PriorityLevel>> {
  const levels: Partial<Record<string, PriorityLevel>> = {};
  for (const id of PRIORITY_IDS) {
    const answer = answers[id];
    if (answer !== undefined && LEVELS.includes(answer))
      levels[id] = answer as PriorityLevel;
  }
  return levels;
}

/** The decision's outcomes in the emphasised order. All of them: an outcome the API did not list goes last. */
export function orderOutcomes(
  decision: Decision,
  emphasis: Emphasis | undefined,
): readonly OutcomeAssessment[] {
  if (!emphasis) return decision.outcomes;
  const rank = new Map(emphasis.outcome_order.map((id, index) => [id, index]));
  const last = emphasis.outcome_order.length;
  return [...decision.outcomes].sort(
    (a, b) => (rank.get(a.outcome_id) ?? last) - (rank.get(b.outcome_id) ?? last),
  );
}

export interface PriorityGap {
  id: string;
  label: string;
  gap: string;
}

/** Each priority that applied, with what we cannot answer for it. */
export function priorityGaps(emphasis: Emphasis): PriorityGap[] {
  return emphasis.priorities_used.map((id, index) => ({
    id,
    label: priorityLabels[id] ?? id,
    gap: emphasis.gaps_for_priorities[index] ?? "",
  }));
}
