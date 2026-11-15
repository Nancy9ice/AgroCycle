import { loadField } from "@/features/field/data/load";
import type { DemoField } from "@/features/field/types";
import { getFieldProfile } from "@/features/profile/get-field-profile";
import type { FieldProfile } from "@/features/profile/types";
import type { Answers } from "@/features/priorities/questions";
import { toEngineConstraints, toEngineProfile } from "./engine-input";
import { ServiceError, apiBaseUrl, offlineEngineAllowed } from "@/lib/api";
import { fetchDecision } from "./api-client";
import { assess } from "./evaluate";
import { plain, plainAll } from "@/lib/plain-words";
import type {
  Decision,
  OutcomeAssessment,
  RuleFinding,
  StrategyAssessment,
} from "./types";

/**
 * Which engine produced a comparison.
 *
 * - `api`: the Python decision engine, run by the AgroCycle API. The authoritative one.
 * - `offline_fallback`: the TypeScript copy inside the web app, used only when no API is configured
 *   (local development, or a deployment that has opted in). It is labelled wherever a result is shown.
 */
export type EngineSource = "api" | "offline_fallback";

export interface ComparisonProvenance {
  source: EngineSource;
  /** The rules version the decision was made with (`decision.rules_version`). */
  rulesVersion: string;
  /** The data version the API served the profile from. Only the API knows it. */
  dataVersion?: string;
  /** When the API ran the comparison. */
  createdAt?: string;
}

export interface Comparison {
  field: DemoField;
  decision: Decision;
  /** True when sample indicator values were fed to the engine (`?preview=sample`). */
  preview: boolean;
  /** Set when the API ran the comparison and stored the result for /ask. */
  analysisId?: string;
  /** Which engine, which rules and which data produced this. Shown on the compare screen and in the brief. */
  provenance: ComparisonProvenance;
  /**
   * The field profile behind the comparison, for the evidence ledger and the adviser brief. Absent when
   * the profile service did not answer; the comparison itself does not depend on it.
   */
  profile?: FieldProfile;
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

/** The profile is context for the ledger and the brief, so a profile failure must not take the comparison down. */
async function profileOrUndefined(fieldId: string): Promise<FieldProfile | undefined> {
  try {
    return await getFieldProfile(fieldId);
  } catch (error) {
    if (error instanceof ServiceError) return undefined;
    throw error;
  }
}

/**
 * Compares the three strategies for one field. Returns undefined for unknown fields.
 *
 * The API is the authoritative decision engine:
 *
 * - With `AGROCYCLE_API_URL` set, it asks the API (`POST /fields/{id}/compare`), which runs `engine/` on
 *   the server against the field's real profile. A failing service throws `ServiceError`; it never falls
 *   back quietly to the copy below.
 * - Without it, it uses the TypeScript copy of the engine and says so (`provenance.source ===
 *   "offline_fallback"`). `engine-parity.test.ts` and the API's `test_web_export_is_current.py` keep that
 *   copy's rules and logic equal to the Python ones, but it sees a thinner profile, so it is for local
 *   development and demos with no backend. In production it refuses unless the deployment opts in
 *   (`offlineEngineAllowed`).
 */
export async function getComparison(
  fieldId: string,
  answers: Answers,
  options: { preview: boolean },
): Promise<Comparison | undefined> {
  const field = await loadField(fieldId);
  if (!field) return undefined;

  const constraints = toEngineConstraints(answers);
  const baseUrl = apiBaseUrl();
  if (baseUrl) {
    const [result, profile] = await Promise.all([
      fetchDecision(baseUrl, fieldId, constraints, options.preview),
      profileOrUndefined(fieldId),
    ]);
    if (!result) return undefined;
    return {
      field,
      decision: withPlainWords(result.decision),
      preview: result.preview,
      analysisId: result.analysis_id,
      profile,
      provenance: {
        source: "api",
        rulesVersion: result.decision.rules_version,
        dataVersion: result.data_version || undefined,
        createdAt: result.created_at,
      },
    };
  }

  if (!offlineEngineAllowed()) {
    console.error(
      "AGROCYCLE_API_URL is not set and the offline engine is not allowed in production. " +
        "Set AGROCYCLE_API_URL, or AGROCYCLE_ALLOW_OFFLINE_ENGINE=true to run the offline copy on purpose.",
    );
    throw new ServiceError("The comparison service is not configured.");
  }

  const profile = await getFieldProfile(fieldId);
  if (!profile) return undefined;
  const decision = withPlainWords(
    assess(toEngineProfile(field, profile, { sample: options.preview }), constraints),
  );
  return {
    field,
    decision,
    preview: options.preview,
    profile,
    provenance: { source: "offline_fallback", rulesVersion: decision.rules_version },
  };
}
