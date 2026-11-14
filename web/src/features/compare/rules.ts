/**
 * DS2's rule table, exported by `npm run sync:engine` from `engine/rules/strategy_rules.py` so that
 * no rule text is retyped here. Typed loosely at the JSON edge, strictly everywhere else.
 */
import type { EvidenceTypeId } from "@/domain/evidence";
import type { RuleEffect, StrategyKey } from "./types";
import table from "./data/rules.generated.json";

export type Operator =
  "equals" | "not_equals" | "lt" | "lte" | "gt" | "gte" | "in" | "not_in" | "is_unknown";

export interface ApplicabilityRule {
  rule_id: string;
  outcome_id: string;
  context_key: string;
  operator: Operator;
  value: boolean | number | string | readonly string[] | null;
  effect: RuleEffect;
  condition_text: string;
  rationale: string;
  review: "not_expert_reviewed" | "expert_reviewed";
}

export interface OutcomeEvidence {
  outcome_id: string;
  label: string;
  claimable: boolean;
  evidence_type: EvidenceTypeId | null;
  source: string | null;
  what_may_be_said: string;
  what_may_not_be_said: string;
}

export interface StrategyProfile {
  strategy_id: StrategyKey;
  label: string;
  rotation: string;
  operational_requirements: readonly string[];
}

export interface CropClaim {
  claim_id: string;
  crop: string;
  claim: string;
  status: "sourced" | "research_needed";
  note: string;
}

export interface RuleTable {
  rulesVersion: string;
  wholeComparisonTarget: string;
  severity: readonly RuleEffect[];
  requiredIndicators: readonly string[];
  standingLimitations: readonly string[];
  strategies: readonly StrategyProfile[];
  outcomes: readonly OutcomeEvidence[];
  rules: readonly ApplicabilityRule[];
  cropClaims: readonly CropClaim[];
}

export const ruleTable = table as unknown as RuleTable;
