import { describe, expect, it } from "vitest";
import parity from "./data/engine-parity.generated.json";
import { assess, type EngineConstraints, type EngineProfile } from "./evaluate";
import { ruleTable } from "./rules";

/**
 * The port in `evaluate.ts` must give the same answer as the real Python engine.
 * Fixture: `npm run sync:engine` (runs `engine/decision.py` over 7 profiles x 81 constraint combinations).
 */

type Partial_ = Partial<EngineProfile>;

const profileFor = (name: string): EngineProfile => {
  const given = (parity.profiles as Record<string, Partial_>)[name];
  return {
    field_id: "parity",
    boundary_source: "demo",
    crop_history_summary: "parity fixture",
    county: null,
    crop_history_is_maize_soybean: null,
    gdd_season_difference_vs_marsden: null,
    frost_free_days: null,
    dominant_drainage_class: null,
    indicator_statuses: {},
    ...given,
  };
};

const summarise = (decision: ReturnType<typeof assess>) => ({
  o: decision.outcome,
  r: decision.outcome_reason,
  u: decision.unknowns,
  s: decision.strategies.map((s) => [
    s.strategy_id,
    s.feasibility,
    s.findings.map((f) => f.rule_id),
  ]),
  x: decision.outcomes.map((o) => [
    o.outcome_id,
    o.status,
    o.findings.map((f) => f.rule_id),
    o.statement !== null,
  ]),
});

describe("TypeScript engine port", () => {
  it("uses the same rules version as the exported fixture", () => {
    expect(ruleTable.rulesVersion).toBe(parity.rulesVersion);
  });

  it("covers every profile and every constraint combination", () => {
    expect(parity.cases).toHaveLength(Object.keys(parity.profiles).length * 81);
  });

  it("reproduces the Python engine for every case", () => {
    const keys = parity.constraintKeys as (keyof EngineConstraints)[];
    const mismatches: string[] = [];
    for (const testCase of parity.cases) {
      const constraints = {
        priorities: [],
        ...Object.fromEntries(keys.map((key, index) => [key, testCase.c[index]])),
      } as unknown as EngineConstraints;
      const actual = summarise(assess(profileFor(testCase.p), constraints));
      if (JSON.stringify(actual) !== JSON.stringify(testCase.e)) {
        mismatches.push(`${testCase.p} ${JSON.stringify(testCase.c)}`);
      }
    }
    expect(mismatches).toEqual([]);
  });

  it("reaches all three outcomes in the fixture, so the comparison is not vacuous", () => {
    const outcomes = new Set(parity.cases.map((testCase) => testCase.e.o));
    expect([...outcomes].sort()).toEqual([
      "abstention",
      "qualified_comparison",
      "strategy_worth_exploring",
    ]);
  });
});
