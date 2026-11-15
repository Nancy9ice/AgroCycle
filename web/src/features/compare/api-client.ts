import { ServiceError, callApi } from "@/lib/api";
import type { ContextAnswers } from "./engine-input";
import type { EngineConstraints } from "./evaluate";
import type { Decision } from "./types";

/**
 * Calls the API's `POST /fields/{id}/compare` (see `api/README.md`). The request carries the farmer's
 * answers, priorities and context-only answers (hay equipment, storage, labour) and nothing else: the API builds the field's profile, so the browser cannot send a
 * wrong one.
 */

const OUTCOMES = ["strategy_worth_exploring", "qualified_comparison", "abstention"];

/** The API's own response shape, narrowed to what this screen reads. */
export interface CompareApiResponse {
  decision: Decision;
  preview: boolean;
  analysis_id?: string;
  created_at?: string;
  engine_version?: string;
  data_version?: string;
  context_recorded?: ContextAnswers;
  context_note?: string;
}

export function isCompareResponse(value: unknown): value is CompareApiResponse {
  if (typeof value !== "object" || value === null) return false;
  const { decision, preview } = value as Partial<CompareApiResponse>;
  return (
    typeof preview === "boolean" &&
    typeof decision === "object" &&
    decision !== null &&
    OUTCOMES.includes(decision.outcome) &&
    Array.isArray(decision.strategies) &&
    Array.isArray(decision.outcomes) &&
    Array.isArray(decision.unknowns)
  );
}

/**
 * Returns the API's decision, `undefined` if the API says the field does not exist, and throws
 * `ServiceError` for anything else, including a response that does not look like a decision.
 */
export async function fetchDecision(
  baseUrl: string,
  fieldId: string,
  constraints: EngineConstraints,
  preview: boolean,
  context?: ContextAnswers,
): Promise<CompareApiResponse | undefined> {
  const body = await callApi(baseUrl, `/fields/${encodeURIComponent(fieldId)}/compare`, {
    method: "POST",
    body: { ...constraints, ...(context ? { context } : {}), sample_indicators: preview },
  });
  if (body === undefined) return undefined;
  if (!isCompareResponse(body)) {
    throw new ServiceError("The comparison service sent an unexpected answer.");
  }
  return body;
}
