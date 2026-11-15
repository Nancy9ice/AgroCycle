import { describe, expect, it } from "vitest";
import { boundarySourceLabel, fieldName, isDrawn, isKnownEdgeCase } from "./labels";
import type { DemoField } from "./types";

const field = (overrides: Partial<DemoField>): DemoField => ({
  id: "x",
  role: "test",
  county: "Story",
  boundarySource: "demo",
  provenance: "",
  domainNote: "",
  fieldClass: "rotation",
  coverDetail: null,
  areaHa: 10,
  centroid: [0, 0],
  ring: [],
  ...overrides,
});

describe("labels for a boundary the farmer drew", () => {
  it("is called 'Your field', never a demo or test field", () => {
    const drawn = field({ id: "drawn-ab12", role: "drawn", boundarySource: "drawn" });
    expect(fieldName(drawn)).toBe("Your field");
    expect(isDrawn(drawn)).toBe(true);
    expect(boundarySourceLabel.drawn).toBe("Drawn by you");
    expect(isDrawn(field({}))).toBe(false);
  });

  it("is not an edge case until we know it is not a rotation", () => {
    expect(isKnownEdgeCase(field({ fieldClass: "unknown" }))).toBe(false);
    expect(isKnownEdgeCase(field({ fieldClass: "rotation" }))).toBe(false);
    expect(isKnownEdgeCase(field({ fieldClass: "corn" }))).toBe(true);
    expect(isKnownEdgeCase(field({ fieldClass: "mixed" }))).toBe(true);
  });
});
