import { getFieldById } from "@/features/field/data";
import type { DemoField } from "@/features/field/types";
import { getFieldProfile } from "@/features/profile/get-field-profile";
import type { Answers } from "@/features/priorities/questions";
import { toEngineConstraints, toEngineProfile } from "./engine-input";
import { assess } from "./evaluate";
import type { Decision } from "./types";

export interface Comparison {
  field: DemoField;
  decision: Decision;
  /** True when sample indicator values were fed to the engine (`?preview=sample`). */
  preview: boolean;
}

/**
 * Compares the three strategies for one field. Stand-in for `POST /fields/{id}/compare`: it is
 * async so callers already look like they await an API, and it returns the same `Decision` the
 * real engine produces (see `engine-parity.test.ts`). Returns undefined for unknown fields.
 */
export async function getComparison(
  fieldId: string,
  answers: Answers,
  options: { preview: boolean },
): Promise<Comparison | undefined> {
  const field = getFieldById(fieldId);
  const profile = await getFieldProfile(fieldId);
  if (!field || !profile) return undefined;

  const decision = assess(
    toEngineProfile(field, profile, { sample: options.preview }),
    toEngineConstraints(answers),
  );
  return { field, decision, preview: options.preview };
}
