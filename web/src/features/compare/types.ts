/**
 * The comparison contract: what the compare screen needs from `POST /fields/{id}/compare`.
 *
 * It mirrors `engine/decision.py` (`Decision`, rules version 2026-11-14.2) field for field,
 * snake_case included, as `dataclasses.asdict` would serialise it, with `UNKNOWN` as `null`.
 * Keeping the engine's own names means the stand-in in `get-comparison.ts` can be replaced by
 * the real endpoint without touching a component. The UI renders these values; it never
 * decides a status itself.
 */
import type { EvidenceTypeId } from "@/domain/evidence";

/** PRD 8.3: the only three outcomes the engine may return. */
export type DecisionOutcome =
  "strategy_worth_exploring" | "qualified_comparison" | "abstention";

/** What a rule does to an outcome or strategy (`RULE_EFFECTS` in the rule table). */
export type RuleEffect = "in_domain" | "qualified" | "out_of_domain" | "abstain_outcome";

/** Per outcome. `abstained` and `not_assessed` both mean "we do not know", never "neutral". */
export type OutcomeStatus =
  "in_domain" | "qualified" | "abstained" | "out_of_domain" | "not_assessed";

/** Per strategy. `available` means no rule ruled it out, not that it is proven to fit. */
export type Feasibility = "available" | "qualified" | "unavailable";

export type StrategyKey = "A" | "B" | "C";

export interface RuleFinding {
  rule_id: string;
  /** An outcome id, `strategy_b_feasibility`, `strategy_c_feasibility` or `all_outcomes`. */
  target: string;
  effect: RuleEffect;
  condition_text: string;
  rationale: string;
  review: "not_expert_reviewed" | "expert_reviewed";
}

export interface OutcomeAssessment {
  outcome_id: string;
  label: string;
  status: OutcomeStatus;
  claimable: boolean;
  evidence_type: EvidenceTypeId | null;
  source: string | null;
  /** What may be said. `null` whenever the outcome is withheld or not assessed. */
  statement: string | null;
  /** What may not be said. Always present, even when the outcome is withheld. */
  caution: string;
  findings: readonly RuleFinding[];
}

export interface StrategyAssessment {
  strategy_id: StrategyKey;
  label: string;
  rotation: string;
  feasibility: Feasibility;
  operational_requirements: readonly string[];
  findings: readonly RuleFinding[];
}

export interface ConstraintsRecorded {
  manure_access: boolean | null;
  forage_use_or_buyer: boolean | null;
  oat_use_or_buyer: boolean | null;
  small_grain_equipment_or_contractor: boolean | null;
}

export interface Decision {
  field_id: string;
  boundary_source: string;
  crop_history_summary: string;
  outcome: DecisionOutcome;
  outcome_reason: string;
  strategies: readonly StrategyAssessment[];
  outcomes: readonly OutcomeAssessment[];
  /** Context keys and `indicator <id>` entries nobody has established. */
  unknowns: readonly string[];
  constraints_recorded: ConstraintsRecorded;
  priorities_recorded: readonly string[];
  rules_version: string;
  limitations: readonly string[];
}
