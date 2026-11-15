import { describe, expect, it } from "vitest";
import { toEngineConstraints } from "./engine-input";
import { getComparison } from "./get-comparison";
import { toOpenQuestions } from "./open-questions";
import { highlightedOutcomeIds, readPriorities } from "./priority-links";

describe("engine input", () => {
  it("passes unanswered and 'not sure' as unknown, never false", () => {
    const c = toEngineConstraints({ manure: "unsure" });
    expect(c.manure_access).toBeNull();
    expect(c.oat_use_or_buyer).toBeNull();
  });

  it("passes only high priorities", () => {
    const c = toEngineConstraints({ soil: "high", water: "medium", inputs: "high" });
    expect(c.priorities).toEqual(["soil", "inputs"]);
  });
});

describe("getComparison", () => {
  it("abstains for a rotation field today, because no indicator is computed", async () => {
    const result = await getComparison("primary-001", {}, { preview: false });
    expect(result?.decision.outcome).toBe("abstention");
    expect(result?.decision.unknowns).toContain("indicator gdd");
  });

  it("abstains for a field outside the maize-soybean domain, even in preview", async () => {
    const result = await getComparison("test-027", {}, { preview: true });
    expect(result?.decision.outcome).toBe("abstention");
    expect(
      result?.decision.strategies.every((s) => s.feasibility === "unavailable"),
    ).toBe(true);
  });

  it("reaches 'worth exploring' only in preview with every constraint answered yes", async () => {
    const yes = {
      manure: "yes",
      hayOutlet: "own_livestock",
      oatOutlet: "yes",
      grainEquipment: "have",
    };
    expect(
      (await getComparison("primary-001", yes, { preview: true }))?.decision.outcome,
    ).toBe("strategy_worth_exploring");
    expect(
      (await getComparison("primary-001", yes, { preview: false }))?.decision.outcome,
    ).toBe("abstention");
  });

  it("does not let priorities change the outcome", async () => {
    const base = { manure: "no" };
    const a = await getComparison("primary-001", base, { preview: true });
    const b = await getComparison(
      "primary-001",
      { ...base, soil: "high", inputs: "high" },
      { preview: true },
    );
    expect(b?.decision.outcome).toBe(a?.decision.outcome);
    expect(b?.decision.outcomes.map((o) => o.status)).toEqual(
      a?.decision.outcomes.map((o) => o.status),
    );
  });

  it("returns undefined for an unknown field", async () => {
    expect(await getComparison("nope", {}, { preview: false })).toBeUndefined();
  });
});

describe("open questions", () => {
  it("splits what the farmer can answer from missing data and keeps unmapped keys visible", () => {
    const items = toOpenQuestions(["manure_access", "frost_free_days", "something_new"]);
    expect(items.map((i) => i.kind)).toEqual(["you", "data", "data"]);
    expect(items[0].questionId).toBe("manure");
    expect(items[2].text).toBe("something_new");
  });
});

describe("priorities", () => {
  it("says soil cannot be spoken to, and highlights its outcomes", async () => {
    const result = await getComparison(
      "primary-001",
      { soil: "high" },
      { preview: true },
    );
    const [soil] = readPriorities(result!.decision);
    expect(soil.related.length).toBe(2);
    expect(soil.speakable).toHaveLength(0);
    expect(highlightedOutcomeIds(result!.decision).has("soil_carbon_change")).toBe(true);
  });
});

describe("missing-measurement note", () => {
  it("is shown only when the engine lists a required measurement as unknown", async () => {
    const { hasMissingIndicators } = await import("./labels");
    const noData = await getComparison("primary-001", {}, { preview: false });
    const withData = await getComparison("primary-001", {}, { preview: true });
    expect(hasMissingIndicators(noData!.decision)).toBe(true);
    // Once all four measurements are known, the note must not claim data is missing, even if other
    // things (unanswered farm questions) are still unknown.
    expect(hasMissingIndicators(withData!.decision)).toBe(false);
    expect(withData!.decision.unknowns.length).toBeGreaterThan(0);
  });
});
