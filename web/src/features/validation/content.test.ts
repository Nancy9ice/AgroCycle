import { describe, expect, it } from "vitest";
import { checkKinds, countByKind, unreconciled, validationRows } from "./content";

describe("validation content", () => {
  it("has the nine PRD §11 components, each once", () => {
    expect(validationRows).toHaveLength(9);
    expect(new Set(validationRows.map((row) => row.id)).size).toBe(9);
  });

  it("states all four kinds of evidence for every row, never merged", () => {
    for (const row of validationRows) {
      for (const kind of checkKinds) {
        expect(["done", "partly", "none"], `${row.id} ${kind.id}`).toContain(
          row.kinds[kind.id],
        );
      }
    }
  });

  it("gives every row a result, a limit and a source in the repository", () => {
    for (const row of validationRows) {
      expect(row.checked.length).toBeGreaterThan(20);
      expect(row.result.length).toBeGreaterThan(5);
      expect(row.doesNotShow.length).toBeGreaterThan(20);
      expect(row.source.length).toBeGreaterThan(5);
    }
  });

  it("never describes an internal test as 'validated'", () => {
    const text = validationRows.map((r) => `${r.checked} ${r.result}`).join(" ");
    expect(text).not.toMatch(/validated/i);
  });

  it("derives the summary from the rows", () => {
    const counts = countByKind(validationRows);
    expect(counts.internal.done).toBe(
      validationRows.filter((r) => r.kinds.internal === "done").length,
    );
    expect(counts.internal.total).toBe(9);
  });

  it("claims no independent reference and no expert review anywhere, because none is recorded", () => {
    const counts = countByKind(validationRows);
    expect(counts.independent.done + counts.independent.partly).toBe(0);
    expect(counts.expert.done + counts.expert.partly).toBe(0);
  });

  it("keeps the unreconciled Marsden result with both numbers", () => {
    expect(unreconciled.body).toContain("80");
    expect(unreconciled.body).toContain("74.5");
  });
});
