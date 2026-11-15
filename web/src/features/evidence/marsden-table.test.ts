import { describe, expect, it } from "vitest";
import { buildMarsdenLines, formatFigure, type MarsdenRow } from "./marsden-table";

const row = (rotation: string, metric: string, value: number): MarsdenRow => ({
  rotation,
  metric,
  value,
  unit: "u",
  evidence_type: "experimental",
  source_id: "pone",
});

describe("buildMarsdenLines", () => {
  const rows = [
    row("2-yr", "herbicide", 1.924889),
    row("2-yr", "applied_n", 74.5),
    row("3-yr", "applied_n", 56.556),
    row("4-yr", "applied_n", 40.806),
    row("2-yr", "manufactured_n", 74.5),
  ];

  it("makes one line per measure with a figure per rotation, in a fixed order", () => {
    const lines = buildMarsdenLines(rows);
    expect(lines.map((l) => l.metric)).toEqual([
      "manufactured_n",
      "applied_n",
      "herbicide",
    ]);
    expect(lines[1].values).toEqual({ "2-yr": 74.5, "3-yr": 56.556, "4-yr": 40.806 });
  });

  it("never calls applied nitrogen 'total' nitrogen, and says herbicide is a mass", () => {
    const labels = buildMarsdenLines(rows).map((l) => l.label.toLowerCase());
    expect(labels.join(" ")).not.toContain("total");
    expect(labels.find((l) => l.includes("herbicide"))).toContain("not toxicity");
  });

  it("leaves a missing rotation absent rather than inventing a zero", () => {
    const [line] = buildMarsdenLines([row("2-yr", "manure_n", 0)]);
    expect(line.values).toEqual({ "2-yr": 0 });
    expect("3-yr" in line.values).toBe(false);
  });

  it("keeps a measure it does not know, labelled as sent", () => {
    const [line] = buildMarsdenLines([row("2-yr", "soil_carbon", 1)]);
    expect(line.label).toBe("soil carbon");
  });
});

describe("formatFigure", () => {
  it("shows herbicide to three decimals and nitrogen to one", () => {
    expect(formatFigure("herbicide", 1.924889)).toBe("1.925");
    expect(formatFigure("applied_n", 56.556)).toBe("56.6");
  });
});
