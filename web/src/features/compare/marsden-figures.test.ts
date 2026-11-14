import { describe, expect, it } from "vitest";
import { marsdenFigures } from "./marsden-figures";
import { ruleTable } from "./rules";

describe("Marsden figures", () => {
  for (const [outcomeId, figures] of Object.entries(marsdenFigures)) {
    it(`${outcomeId}: every figure appears in DS2's statement`, () => {
      const outcome = ruleTable.outcomes.find((o) => o.outcome_id === outcomeId);
      expect(outcome, `${outcomeId} is in the rule table`).toBeDefined();
      for (const row of figures.rows) {
        for (const value of Object.values(row.values)) {
          expect(outcome!.what_may_be_said).toContain(String(value));
        }
      }
    });
  }

  it("only attaches figures to claimable outcomes", () => {
    for (const outcomeId of Object.keys(marsdenFigures)) {
      const outcome = ruleTable.outcomes.find((o) => o.outcome_id === outcomeId);
      expect(outcome?.claimable).toBe(true);
    }
  });
});
