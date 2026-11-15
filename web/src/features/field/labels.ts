import type { DemoField, FieldClass } from "./types";

export const fieldClassLabel: Record<FieldClass, string> = {
  rotation: "Corn–soybean rotation",
  corn: "Continuous corn",
  pasture: "Pasture or hay",
  mixed: "Mixed, no rotation",
};

/** True for the fields inside the supported decision (a corn–soybean rotation). */
export const isInDomain = (field: DemoField) => field.fieldClass === "rotation";

/** Short human name: "Story demo field" or "Test field 014". */
export function fieldName(field: DemoField): string {
  if (field.role === "primary") return `${field.county} demo field`;
  return `Test field ${field.id.replace(/^test-/, "")}`;
}

export const boundarySourceLabel: Record<DemoField["boundarySource"], string> = {
  demo: "Demonstration polygon",
  real: "Real boundary",
};
