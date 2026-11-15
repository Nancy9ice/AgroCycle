import { describe, expect, it } from "vitest";
import { evidenceLayers } from "@/domain/evidence";
import { buildEvidenceLedger, layerForOutcome } from "./evidence-ledger";
import { getComparison } from "./get-comparison";

const allYes = {
  manure: "yes",
  hayOutlet: "can_sell",
  oatOutlet: "yes",
  grainEquipment: "have",
};

const ledgerFor = async (answers: Record<string, string>, preview: boolean) => {
  const comparison = (await getComparison("primary-001", answers, { preview }))!;
  return {
    comparison,
    ledger: buildEvidenceLedger(comparison.decision, comparison.profile, { preview }),
  };
};

const layer = (ledger: ReturnType<typeof buildEvidenceLedger>, id: string) =>
  ledger.layers.find((entry) => entry.layer.id === id)!;

describe("evidence ledger", () => {
  it("has the six layers, numbered in order", async () => {
    const { ledger } = await ledgerFor({}, false);
    expect(ledger.layers.map((l) => l.layer.id)).toEqual(evidenceLayers.map((l) => l.id));
    expect(ledger.layers.map((l) => l.number)).toEqual([1, 2, 3, 4, 5, 6]);
  });

  it("files every outcome exactly once", async () => {
    for (const [answers, preview] of [
      [{}, false],
      [allYes, true],
    ] as const) {
      const { comparison, ledger } = await ledgerFor(answers, preview);
      const filed = ledger.layers.flatMap((l) =>
        l.items.filter((i) => i.id.startsWith("outcome-")).map((i) => i.id),
      );
      expect(filed.sort()).toEqual(
        comparison.decision.outcomes.map((o) => `outcome-${o.outcome_id}`).sort(),
      );
    }
  });

  it("puts the Marsden figures under the experiment and the paper's findings under 'published'", async () => {
    const { ledger } = await ledgerFor(allYes, true);
    const experiment = layer(ledger, "marsden_experiment").items.map((i) => i.id);
    const published = layer(ledger, "published_finding").items.map((i) => i.id);
    expect(experiment).toEqual([
      "outcome-applied_n_reduction",
      "outcome-herbicide_reduction",
    ]);
    expect(published).toContain("outcome-yield_parity");
    expect(published).not.toContain("outcome-applied_n_reduction");
  });

  it("says benefits come from research, not the field, when a finding is shown", async () => {
    const { ledger } = await ledgerFor(allYes, true);
    expect(ledger.headline).toMatch(/comes from research/);
    expect(ledger.headline).toMatch(/not from measurements of your field/);
  });

  it("says no benefit statement is shown when every finding is held back", async () => {
    const { ledger } = await ledgerFor({}, false);
    expect(ledger.headline).toMatch(/No statement about benefits/);
    const held = layer(ledger, "marsden_experiment").items;
    expect(held.every((i) => i.state === "withheld")).toBe(true);
  });

  it("lists what nobody has established as missing, not as fine", async () => {
    const { ledger } = await ledgerFor({}, false);
    const derived = layer(ledger, "field_derived").items;
    expect(derived.find((i) => i.id === "input-indicator gdd")?.state).toBe("missing");
    const answers = layer(ledger, "assumed_or_unknown").items.filter((i) =>
      i.id.startsWith("answer-"),
    );
    expect(answers).toHaveLength(4);
    expect(answers.every((i) => i.state === "missing")).toBe(true);
  });

  it("never shows a sample preview value as real", async () => {
    const { ledger } = await ledgerFor(allYes, true);
    const inputs = ledger.layers.flatMap((l) =>
      l.items.filter((i) => i.id.startsWith("input-")),
    );
    const byId = (id: string) => inputs.find((i) => i.id === `input-${id}`)?.state;
    expect(byId("gdd_season_difference_vs_marsden")).toBe("sample");
    expect(byId("frost_free_days")).toBe("sample");
    expect(byId("indicator om_r_0_30cm")).toBe("sample");
    // Real facts stay real, and drainage is not sampled, so it stays unknown.
    expect(byId("county")).toBe("in_comparison");
    expect(byId("crop_history_is_maize_soybean")).toBe("in_comparison");
    expect(byId("dominant_drainage_class")).toBe("missing");
    expect(ledger.headline).toMatch(/^Sample preview/);
  });

  it("marks real inputs as used outside the preview only when they are known", async () => {
    const { ledger } = await ledgerFor({}, false);
    const county = layer(ledger, "field_retrieved").items.find(
      (i) => i.id === "input-county",
    );
    expect(county?.state).toBe("in_comparison");
    expect(ledger.headline).not.toMatch(/Sample preview/);
  });

  it("keeps outcomes with no data under 'assumed or unknown', as not assessed", async () => {
    const { comparison, ledger } = await ledgerFor(allYes, true);
    const unassessed = comparison.decision.outcomes.filter((o) => !o.claimable);
    expect(unassessed.length).toBeGreaterThan(0);
    for (const outcome of unassessed) {
      expect(layerForOutcome(outcome)).toBe("assumed_or_unknown");
      const item = layer(ledger, "assumed_or_unknown").items.find(
        (i) => i.id === `outcome-${outcome.outcome_id}`,
      );
      expect(item?.state).toBe("not_assessed");
    }
  });

  it("records what the farmer said and the priorities they marked high", async () => {
    const { ledger } = await ledgerFor({ manure: "no", soil: "high" }, true);
    const items = layer(ledger, "assumed_or_unknown").items;
    expect(items.find((i) => i.id === "answer-manure")?.detail).toBe("You said no.");
    expect(items.find((i) => i.id === "priorities")?.detail).toMatch(
      /Look after the soil/,
    );
  });

  it("names the crop-history period and source when the profile is loaded", async () => {
    const { ledger } = await ledgerFor({}, false);
    const crop = layer(ledger, "field_retrieved").items.find(
      (i) => i.id === "crop-history",
    );
    expect(crop?.label).toMatch(/\d{4} to \d{4}/);
    expect(crop?.evidenceType).toBe("classified");
  });

  it("says the rules are unreviewed", async () => {
    const { ledger } = await ledgerFor({}, false);
    const review = layer(ledger, "assumed_or_unknown").items.find(
      (i) => i.id === "rules-review",
    );
    expect(review?.detail).toMatch(/reviewed by an agronomist/);
  });
});
