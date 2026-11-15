import { getFieldById } from "@/features/field/data";
import type { DemoField } from "@/features/field/types";
import { getFieldProfile } from "@/features/profile/get-field-profile";
import type { Answers } from "@/features/priorities/questions";
import { toEngineConstraints, toEngineProfile } from "./engine-input";
import { apiBaseUrl } from "@/lib/api";
import { fetchDecision } from "./api-client";
import { assess } from "./evaluate";
import { plain, plainAll } from "@/lib/plain-words";
import type {
  Decision,
  OutcomeAssessment,
  RuleFinding,
  StrategyAssessment,
} from "./types";

export interface Comparison {
  field: DemoField;
  decision: Decision;
  /** True when sample indicator values were fed to the engine (`?preview=sample`). */
  preview: boolean;
  /** Set when the API ran the comparison and stored the result for /ask. */
  analysisId?: string;
}

const plainFinding = (finding: RuleFinding): RuleFinding => ({
  ...finding,
  condition_text: plain(finding.condition_text),
  rationale: plain(finding.rationale),
});

/**
 * Says the engine's sentences in a farmer's words (`lib/plain-words.ts`). Ids, statuses, labels used for
 * matching and the unknowns list are left exactly as the engine sent them.
 */
export function withPlainWords(decision: Decision): Decision {
  return {
    ...decision,
    outcome_reason: plain(decision.outcome_reason),
    crop_history_summary: plain(decision.crop_history_summary),
    limitations: plainAll(decision.limitations),
    strategies: decision.strategies.map((strategy): StrategyAssessment => ({
      ...strategy,
      operational_requirements: plainAll(strategy.operational_requirements),
      findings: strategy.findings.map(plainFinding),
    })),
    outcomes: decision.outcomes.map((outcome): OutcomeAssessment => ({
      ...outcome,
      label: plain(outcome.label),
      statement: outcome.statement === null ? null : plain(outcome.statement),
      caution: plain(outcome.caution),
      caution_reference: plain(outcome.caution_reference),
      findings: outcome.findings.map(plainFinding),
    })),
  };
}

/**
 * Compares the three strategies for one field. Returns undefined for unknown fields.
 *
 * - With `AGROCYCLE_API_URL` set, it asks the API (`POST /fields/{id}/compare`), which runs DS2's engine
 *   on the server. A failing service throws `ServiceError`; it does not fall back quietly.
 * - Without it, it uses the TypeScript copy of the engine, which `engine-parity.test.ts` and the API's
 *   tests keep equal to the Python one. This is what runs in local development with no API.
 */
export async function getComparison(
  fieldId: string,
  answers: Answers,
  options: { preview: boolean },
): Promise<Comparison | undefined> {
  const field = getFieldById(fieldId);
  if (!field) return undefined;

  const constraints = toEngineConstraints(answers);
  const baseUrl = apiBaseUrl();
  if (baseUrl) {
    const result = await fetchDecision(baseUrl, fieldId, constraints, options.preview);
    return (
      result && {
        field,
        decision: withPlainWords(result.decision),
        preview: result.preview,
        analysisId: result.analysis_id,
      }
    );
  }

  const profile = await getFieldProfile(fieldId);
  if (!profile) return undefined;
  const decision = withPlainWords(
    assess(toEngineProfile(field, profile, { sample: options.preview }), constraints),
  );
  return { field, decision, preview: options.preview };
}
