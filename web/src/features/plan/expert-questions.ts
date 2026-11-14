import { ruleTable } from "@/features/compare/rules";
import type { Decision, RuleEffect } from "@/features/compare/types";
import { toOpenQuestions } from "@/features/compare/open-questions";
import { optionLabel, questions, type Answers } from "@/features/priorities/questions";

export interface AdviserQuestion {
  id: string;
  text: string;
  /** Where the question comes from, for traceability. */
  source: "answer" | "context" | "rule" | "data" | "claim" | "standing";
}

const askAfter: Record<RuleEffect, string> = {
  out_of_domain: "Is there local evidence that covers this case?",
  abstain_outcome: "What would settle it for this field?",
  qualified: "How much does this matter on this land?",
  in_domain: "",
};

/** Always asked: they come from the limits every result carries, not from a rule firing. */
const standing: readonly AdviserQuestion[] = [
  {
    id: "standing-site",
    text: "The figures come from one research site over nine seasons. Do they hold on my soils and in my weather?",
    source: "standing",
  },
  {
    id: "standing-rules",
    text: "The rules behind this have not been reviewed by an agronomist. Do they make sense for my county?",
    source: "standing",
  },
  {
    id: "standing-money",
    text: "No profit is calculated here. What would each option cost me, and what would it earn?",
    source: "standing",
  },
];

/**
 * Constraints no rule reads (hay equipment, storage, extra help). They cannot change the result,
 * because DS2 has no sourced rule for them, but a limiting answer is still something an adviser
 * should hear about. These answers make a question, never an outcome.
 */
const contextOnly: Readonly<Record<string, readonly string[]>> = {
  hayEquipment: ["no", "unsure"],
  storage: ["no", "unsure"],
  labour: ["little"],
};

/**
 * Turns a decision into questions to take to someone who knows the land (PRD 5.2 step 8).
 * Derived from what the engine returned, so a new rule needs no change here: each fired rule
 * contributes its own sentence. Order: what only you can answer, then rules, then data gaps,
 * then unsourced claims, then the standing questions.
 */
export function buildAdviserQuestions(
  decision: Decision,
  answers: Answers = {},
): AdviserQuestion[] {
  const open = toOpenQuestions(decision.unknowns);
  const fromAnswers = open
    .filter((item) => item.kind === "you")
    .map((item): AdviserQuestion => ({
      id: `answer-${item.key}`,
      text: `${item.text} (You have not said. Find out before deciding.)`,
      source: "answer",
    }));

  const fromContext = questions.flatMap((question): AdviserQuestion[] => {
    const answer = answers[question.id as keyof Answers];
    if (!answer || !contextOnly[question.id]?.includes(answer)) return [];
    return [
      {
        id: `context-${question.id}`,
        text: `${question.label}: you answered “${optionLabel(question, answer)}”. ${"why" in question ? question.why : ""} Does that change which option is realistic for you? (This did not change the result above.)`,
        source: "context",
      },
    ];
  });

  const seen = new Set<string>();
  const fromRules: AdviserQuestion[] = [];
  for (const finding of [
    ...decision.outcomes.flatMap((o) => o.findings),
    ...decision.strategies.flatMap((s) => s.findings),
  ]) {
    if (finding.effect === "in_domain" || seen.has(finding.rule_id)) continue;
    seen.add(finding.rule_id);
    fromRules.push({
      id: `rule-${finding.rule_id}`,
      text: `${finding.condition_text} ${askAfter[finding.effect]}`,
      source: "rule",
    });
  }

  const fromData = open
    .filter((item) => item.kind === "data")
    .map((item): AdviserQuestion => ({
      id: `data-${item.key}`,
      text: `We do not have: ${item.text.charAt(0).toLowerCase()}${item.text.slice(1)}. Can you find it for this field?`,
      source: "data",
    }));

  const fromClaims = ruleTable.cropClaims
    .filter((claim) => claim.status === "research_needed")
    .map((claim): AdviserQuestion => ({
      id: `claim-${claim.claim_id}`,
      text: `Can you point me to a source for this? “${claim.claim}”`,
      source: "claim",
    }));

  return [
    ...fromAnswers,
    ...fromContext,
    ...fromRules,
    ...fromData,
    ...fromClaims,
    ...standing,
  ];
}
