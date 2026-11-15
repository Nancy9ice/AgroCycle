import type {
  Decision,
  DecisionOutcome,
  Feasibility,
  OutcomeStatus,
  RuleFinding,
} from "./types";

/** Plain-language copy for the engine's states. The engine decides the state; this only names it. */

export const outcomeCopy: Record<DecisionOutcome, { title: string; summary: string }> = {
  strategy_worth_exploring: {
    title: "Worth exploring further",
    summary:
      "At least one longer rotation looks like a reasonable candidate for local evaluation, given what you told us. This is not a recommendation, and we do not rank the options.",
  },
  qualified_comparison: {
    title: "A comparison, with caveats",
    summary:
      "The options can be compared, but the evidence cannot separate them. Some things are unknown or may not carry over to your farm. Take the open questions below to someone who knows your land.",
  },
  abstention: {
    title: "We cannot compare these options for this field yet",
    summary:
      "There is not enough evidence, or this field is outside what the evidence covers. We would rather say so than guess.",
  },
};

export const outcomeStatusCopy: Record<
  OutcomeStatus,
  { label: string; tone: "good" | "caution" | "stop" | "neutral"; glyph: string }
> = {
  in_domain: { label: "The evidence applies", tone: "good", glyph: "✓" },
  qualified: { label: "Applies, with caveats", tone: "caution", glyph: "!" },
  abstained: { label: "Held back: needs more information", tone: "stop", glyph: "?" },
  out_of_domain: { label: "Does not carry over to your farm", tone: "stop", glyph: "×" },
  not_assessed: { label: "Not assessed", tone: "neutral", glyph: "–" },
};

export const feasibilityCopy: Record<
  Feasibility,
  { label: string; tone: "good" | "caution" | "stop"; glyph: string }
> = {
  available: { label: "Nothing in your answers rules it out", tone: "good", glyph: "✓" },
  qualified: { label: "Needs checking", tone: "caution", glyph: "!" },
  unavailable: { label: "Not available for you", tone: "stop", glyph: "×" },
};

/** True when the field itself is outside the evidence, so no option is offered at all. */
export const comparisonBlocked = (decision: Decision): boolean =>
  decision.strategies.every((strategy) => strategy.feasibility === "unavailable");

/** True when the engine lists any required measurement as unknown, i.e. the data is what is missing. */
export const hasMissingIndicators = (decision: Decision): boolean =>
  decision.unknowns.some((unknown) => unknown.startsWith("indicator "));

const severityOrder = [
  "out_of_domain",
  "abstain_outcome",
  "qualified",
  "in_domain",
] as const;

/** Every distinct reason the engine fired, most serious first, each once. */
export function distinctFindings(decision: Decision): RuleFinding[] {
  const seen = new Map<string, RuleFinding>();
  for (const finding of [
    ...decision.outcomes.flatMap((outcome) => outcome.findings),
    ...decision.strategies.flatMap((strategy) => strategy.findings),
  ]) {
    if (finding.effect !== "in_domain") seen.set(finding.rule_id, finding);
  }
  return [...seen.values()].sort(
    (a, b) => severityOrder.indexOf(a.effect) - severityOrder.indexOf(b.effect),
  );
}

export const effectLabel: Record<RuleFinding["effect"], string> = {
  out_of_domain: "Does not carry over",
  abstain_outcome: "Held back",
  qualified: "Caveat",
  in_domain: "Applies",
};
