import { getFieldById } from "@/features/field/data";
import type { DemoField } from "@/features/field/types";
import { getFieldProfile } from "@/features/profile/get-field-profile";
import type { Answers } from "@/features/priorities/questions";
import { toEngineConstraints, toEngineProfile } from "./engine-input";
import { apiBaseUrl, fetchDecision } from "./api-client";
import { assess } from "./evaluate";
import type { Decision } from "./types";

export interface Comparison {
  field: DemoField;
  decision: Decision;
  /** True when sample indicator values were fed to the engine (`?preview=sample`). */
  preview: boolean;
}

/**
 * Compares the three strategies for one field. Returns undefined for unknown fields.
 *
 * - With `AGROCYCLE_API_URL` set, it asks the API (`POST /fields/{id}/compare`), which runs DS2's engine
 *   on the server. A failing service throws `ComparisonServiceError`; it does not fall back quietly.
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
    return result && { field, decision: result.decision, preview: result.preview };
  }

  const profile = await getFieldProfile(fieldId);
  if (!profile) return undefined;
  const decision = assess(
    toEngineProfile(field, profile, { sample: options.preview }),
    constraints,
  );
  return { field, decision, preview: options.preview };
}
