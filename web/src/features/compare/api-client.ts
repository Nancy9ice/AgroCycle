import type { EngineConstraints } from "./evaluate";
import type { Decision } from "./types";

/**
 * Calls the API's `POST /fields/{id}/compare` (see `api/README.md`). Server-side only: it reads
 * `AGROCYCLE_API_URL`, which is deliberately not a `NEXT_PUBLIC_` variable, so the browser never calls it
 * and no CORS or key handling is needed.
 *
 * The request carries the farmer's answers and priorities and nothing else. The API builds the field's
 * profile, so the browser cannot send a wrong one.
 */

const OUTCOMES = ["strategy_worth_exploring", "qualified_comparison", "abstention"];

export class ComparisonServiceError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "ComparisonServiceError";
  }
}

/** The API's own response shape, narrowed to what this screen reads. */
interface CompareApiResponse {
  decision: Decision;
  preview: boolean;
}

function isCompareResponse(value: unknown): value is CompareApiResponse {
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

export const apiBaseUrl = (): string | undefined =>
  process.env.AGROCYCLE_API_URL?.replace(/\/+$/, "") || undefined;

/**
 * Returns the API's decision, `undefined` if the API says the field does not exist, and throws
 * `ComparisonServiceError` for anything else: an unreachable service, an error status, or a response
 * that does not look like a decision. A broken service must be visible, never a silent guess.
 */
export async function fetchDecision(
  baseUrl: string,
  fieldId: string,
  constraints: EngineConstraints,
  preview: boolean,
): Promise<CompareApiResponse | undefined> {
  const { priorities, ...answers } = constraints;
  let response: Response;
  try {
    response = await fetch(`${baseUrl}/fields/${encodeURIComponent(fieldId)}/compare`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ ...answers, priorities, sample_indicators: preview }),
      cache: "no-store",
      signal: AbortSignal.timeout(10_000),
    });
  } catch {
    throw new ComparisonServiceError("The comparison service could not be reached.");
  }

  if (response.status === 404) return undefined;
  if (!response.ok) {
    throw new ComparisonServiceError(
      `The comparison service answered with an error (${response.status}).`,
    );
  }

  const body: unknown = await response.json().catch(() => null);
  if (!isCompareResponse(body)) {
    throw new ComparisonServiceError("The comparison service sent an unexpected answer.");
  }
  return body;
}
