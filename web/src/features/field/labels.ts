import type { DemoField, FieldClass } from "./types";

export const fieldClassLabel: Record<FieldClass, string> = {
  rotation: "Corn–soybean rotation",
  corn: "Continuous corn",
  pasture: "Pasture or hay",
  mixed: "Mixed, no rotation",
  unknown: "Not provided yet",
};

/** True for the fields inside the supported decision (a corn–soybean rotation). */
export const isInDomain = (field: DemoField) => field.fieldClass === "rotation";

/** True once we know the field is NOT a rotation. A field with no class yet is unknown, not an edge case. */
export const isKnownEdgeCase = (field: DemoField) =>
  field.fieldClass !== "rotation" && field.fieldClass !== "unknown";

/** Short human name: "Story demo field" or "Test field 014". */
export function fieldName(field: DemoField): string {
  if (field.role === "drawn") return "Your field";
  if (field.role === "primary") return `${field.county} demo field`;
  return `Test field ${field.id.replace(/^test-/, "")}`;
}

export const boundarySourceLabel: Record<DemoField["boundarySource"], string> = {
  demo: "Demonstration polygon",
  real: "Real boundary",
  drawn: "Drawn by you",
};

/** True for a boundary the farmer drew, which has no pre-processed data. */
export const isDrawn = (field: DemoField) => field.role === "drawn";
