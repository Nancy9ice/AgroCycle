/**
 * A TypeScript port of `engine/decision.py` (`assess`), used until BE ships `POST /compare`.
 *
 * It holds no policy: every rule, label and sentence comes from the rule table that DS2 wrote and
 * `npm run sync:engine` exported. `engine-parity.test.ts` requires this port to reproduce the real
 * Python engine for 567 profile and constraint combinations, so a change on either side that is not
 * mirrored fails a test instead of silently diverging.
 *
 * Unknown is `null`, never `false` (PRD 8.5). A known value fires an `is_unknown` rule never, and an
 * unknown value fires nothing except `is_unknown`.
 */
import {
  ruleTable,
  type ApplicabilityRule,
  type OutcomeEvidence,
  type RuleTable,
  type StrategyProfile,
} from "./rules";
import type {
  ConstraintsRecorded,
  Decision,
  DecisionOutcome,
  Feasibility,
  OutcomeAssessment,
  OutcomeStatus,
  RuleEffect,
  RuleFinding,
  StrategyAssessment,
} from "./types";

export interface EngineProfile {
  field_id: string;
  boundary_source: string;
  crop_history_summary: string;
  county: string | null;
  crop_history_is_maize_soybean: boolean | null;
  gdd_season_difference_vs_marsden: number | null;
  frost_free_days: number | null;
  dominant_drainage_class: string | null;
  /** `indicator_id` to `"ok"` or `"unknown"`. A missing entry is unknown. */
  indicator_statuses: Readonly<Record<string, string>>;
}

export interface EngineConstraints extends ConstraintsRecorded {
  priorities: readonly string[];
}

type ContextValue = string | number | boolean | null;
type Context = Readonly<Record<string, ContextValue>>;

const CONSTRAINT_KEYS = [
  "manure_access",
  "forage_use_or_buyer",
  "oat_use_or_buyer",
  "small_grain_equipment_or_contractor",
] as const;

const STATUS_FROM_EFFECT: Record<RuleEffect, OutcomeStatus> = {
  in_domain: "in_domain",
  qualified: "qualified",
  abstain_outcome: "abstained",
  out_of_domain: "out_of_domain",
};

const FEASIBILITY_FROM_EFFECT: Record<RuleEffect, Feasibility> = {
  in_domain: "available",
  qualified: "qualified",
  abstain_outcome: "qualified",
  out_of_domain: "unavailable",
};

const FEASIBILITY_TARGET: Record<string, string> = {
  B: "strategy_b_feasibility",
  C: "strategy_c_feasibility",
};

export function unknownRequiredIndicators(
  profile: EngineProfile,
  table: RuleTable = ruleTable,
): string[] {
  return table.requiredIndicators.filter(
    (indicator) => (profile.indicator_statuses[indicator] ?? "unknown") !== "ok",
  );
}

export function buildContext(
  profile: EngineProfile,
  constraints: EngineConstraints,
  table: RuleTable = ruleTable,
): Context {
  return {
    county: profile.county,
    crop_history_is_maize_soybean: profile.crop_history_is_maize_soybean,
    gdd_season_difference_vs_marsden: profile.gdd_season_difference_vs_marsden,
    frost_free_days: profile.frost_free_days,
    dominant_drainage_class: profile.dominant_drainage_class,
    manure_access: constraints.manure_access,
    forage_use_or_buyer: constraints.forage_use_or_buyer,
    oat_use_or_buyer: constraints.oat_use_or_buyer,
    small_grain_equipment_or_contractor: constraints.small_grain_equipment_or_contractor,
    required_indicators_all_known: unknownRequiredIndicators(profile, table).length === 0,
  };
}

export function ruleApplies(rule: ApplicabilityRule, context: Context): boolean {
  const value = context[rule.context_key] ?? null;
  if (rule.operator === "is_unknown") return value === null;
  if (value === null) return false;

  switch (rule.operator) {
    case "equals":
      return value === rule.value;
    case "not_equals":
      return value !== rule.value;
    case "in":
      return (rule.value as readonly string[]).includes(value as string);
    case "not_in":
      return !(rule.value as readonly string[]).includes(value as string);
    case "lt":
    case "lte":
    case "gt":
    case "gte": {
      if (typeof value !== "number" || typeof rule.value !== "number") {
        throw new TypeError(
          `rule ${rule.rule_id} compares ${rule.context_key} numerically, got ${String(value)}`,
        );
      }
      if (rule.operator === "lt") return value < rule.value;
      if (rule.operator === "lte") return value <= rule.value;
      if (rule.operator === "gt") return value > rule.value;
      return value >= rule.value;
    }
    default:
      throw new Error(
        `rule ${rule.rule_id} uses an unsupported operator: ${rule.operator}`,
      );
  }
}

const toFinding = (rule: ApplicabilityRule): RuleFinding => ({
  rule_id: rule.rule_id,
  target: rule.outcome_id,
  effect: rule.effect,
  condition_text: rule.condition_text,
  rationale: rule.rationale,
  review: rule.review,
});

/** The most severe effect, so `out_of_domain` beats `abstain_outcome` beats `qualified`. */
function worst(effects: readonly RuleEffect[], table: RuleTable): RuleEffect {
  let result: RuleEffect = "in_domain";
  for (const effect of effects) {
    if (table.severity.indexOf(effect) > table.severity.indexOf(result)) result = effect;
  }
  return result;
}

function assessOutcome(
  outcome: OutcomeEvidence,
  findings: readonly RuleFinding[],
  table: RuleTable,
): OutcomeAssessment {
  if (!outcome.claimable) {
    return {
      outcome_id: outcome.outcome_id,
      label: outcome.label,
      status: "not_assessed",
      claimable: false,
      evidence_type: null,
      source: null,
      statement: null,
      caution: outcome.caution,
      caution_reference: outcome.caution_reference,
      findings: [],
    };
  }
  const relevant = findings.filter(
    (finding) =>
      finding.target === outcome.outcome_id ||
      finding.target === table.wholeComparisonTarget,
  );
  const status =
    STATUS_FROM_EFFECT[
      worst(
        relevant.map((f) => f.effect),
        table,
      )
    ];
  const speakable = status === "in_domain" || status === "qualified";
  return {
    outcome_id: outcome.outcome_id,
    label: outcome.label,
    status,
    claimable: true,
    evidence_type: outcome.evidence_type,
    source: outcome.source,
    statement: speakable ? outcome.statement : null,
    caution: outcome.caution,
    caution_reference: outcome.caution_reference,
    findings: relevant,
  };
}

function assessStrategy(
  findings: readonly RuleFinding[],
  strategy: StrategyProfile,
  table: RuleTable,
): StrategyAssessment {
  const target = FEASIBILITY_TARGET[strategy.strategy_id];
  const relevant = target ? findings.filter((finding) => finding.target === target) : [];
  const comparisonBlocked = findings.some(
    (finding) =>
      finding.target === table.wholeComparisonTarget &&
      finding.effect === "out_of_domain",
  );
  const feasibility: Feasibility = comparisonBlocked
    ? "unavailable"
    : FEASIBILITY_FROM_EFFECT[
        worst(
          relevant.map((f) => f.effect),
          table,
        )
      ];
  return {
    strategy_id: strategy.strategy_id,
    label: strategy.label,
    rotation: strategy.rotation,
    feasibility,
    operational_requirements: strategy.operational_requirements,
    findings: relevant,
  };
}

function decide(
  outcomes: readonly OutcomeAssessment[],
  strategies: readonly StrategyAssessment[],
  findings: readonly RuleFinding[],
  table: RuleTable,
): { outcome: DecisionOutcome; reason: string } {
  const blocking = findings.filter(
    (finding) =>
      finding.target === table.wholeComparisonTarget &&
      finding.effect === "out_of_domain",
  );
  if (blocking.length > 0) {
    return {
      outcome: "abstention",
      reason: `the field is outside the supported domain (${blocking.map((f) => f.rule_id).join(", ")})`,
    };
  }

  const claimable = outcomes.filter((outcome) => outcome.claimable);
  const speakable = claimable.filter(
    (outcome) => outcome.status === "in_domain" || outcome.status === "qualified",
  );
  if (speakable.length === 0) {
    return {
      outcome: "abstention",
      reason:
        "no claimable outcome survived the applicability rules, so there is nothing to compare",
    };
  }

  const candidates = strategies.filter(
    (strategy) => strategy.strategy_id !== "A" && strategy.feasibility === "available",
  );
  const unqualified = claimable.filter((outcome) => outcome.status === "in_domain");
  if (candidates.length > 0 && unqualified.length === claimable.length) {
    const names = candidates.map((strategy) => strategy.strategy_id).join(", ");
    return {
      outcome: "strategy_worth_exploring",
      reason: `strategy ${names} is operationally available and every claimable outcome is in domain; this is a candidate for local evaluation, not a recommendation`,
    };
  }

  const withheld = claimable.filter(
    (outcome) => outcome.status !== "in_domain" && outcome.status !== "qualified",
  );
  const detail =
    withheld.length > 0
      ? `${withheld.length} of ${claimable.length} claimable outcomes were withheld`
      : "some dimensions are qualified";
  return {
    outcome: "qualified_comparison",
    reason: `the strategies can be compared but not separated: ${detail}`,
  };
}

/** Compare the three strategies for one field. Returns one of the three PRD 8.3 outcomes. */
export function assess(
  profile: EngineProfile,
  constraints: EngineConstraints,
  table: RuleTable = ruleTable,
): Decision {
  const context = buildContext(profile, constraints, table);
  const findings = table.rules
    .filter((rule) => ruleApplies(rule, context))
    .map(toFinding);

  const outcomes = table.outcomes.map((outcome) =>
    assessOutcome(outcome, findings, table),
  );
  const strategies = table.strategies.map((strategy) =>
    assessStrategy(findings, strategy, table),
  );
  const { outcome, reason } = decide(outcomes, strategies, findings, table);

  const unknownKeys = Object.entries(context)
    .filter(([, value]) => value === null)
    .map(([key]) => key)
    .sort();
  const missingIndicators = unknownRequiredIndicators(profile, table).map(
    (indicator) => `indicator ${indicator}`,
  );

  return {
    field_id: profile.field_id,
    boundary_source: profile.boundary_source,
    crop_history_summary: profile.crop_history_summary,
    outcome,
    outcome_reason: reason,
    strategies,
    outcomes,
    unknowns: [...unknownKeys, ...missingIndicators],
    constraints_recorded: Object.fromEntries(
      CONSTRAINT_KEYS.map((key) => [key, constraints[key]]),
    ) as unknown as ConstraintsRecorded,
    priorities_recorded: constraints.priorities,
    rules_version: table.rulesVersion,
    limitations: table.standingLimitations,
  };
}
