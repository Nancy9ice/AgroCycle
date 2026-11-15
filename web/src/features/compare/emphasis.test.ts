import { describe, expect, it } from "vitest";
import { orderOutcomes, priorityGaps, toPriorityLevels, type Emphasis } from "./emphasis";
import type { Decision, OutcomeAssessment } from "./types";

const outcome = (id: string): OutcomeAssessment =>
  ({
    outcome_id: id,
    label: id,
    status: "in_domain",
    claimable: true,
  }) as OutcomeAssessment;

const decision = (ids: string[]): Decision =>
  ({ outcomes: ids.map(outcome) }) as unknown as Decision;

const emphasis = (overrides: Partial<Emphasis> = {}): Emphasis => ({
  outcome_order: [],
  highlighted: [],
  gaps_for_priorities: [],
  priorities_used: [],
  note: "Your priorities decide what is shown first.",
  ...overrides,
});

describe("toPriorityLevels", () => {
  it("sends exactly what the farmer answered, low included", () => {
    expect(toPriorityLevels({ soil: "high", water: "medium", inputs: "low" })).toEqual({
      soil: "high",
      water: "medium",
      inputs: "low",
    });
  });

  it("leaves out a priority that was not answered: silence is not 'low'", () => {
    expect(toPriorityLevels({ soil: "high" })).toEqual({ soil: "high" });
    expect(toPriorityLevels({})).toEqual({});
  });

  it("ignores anything that is not a priority or not a level", () => {
    expect(
      toPriorityLevels({ manure: "yes", soil: "very high", labour: "some" }),
    ).toEqual({});
  });
});

describe("orderOutcomes", () => {
  const original = [
    "soil_carbon_change",
    "nitrate_leaching_reduction",
    "applied_n_reduction",
    "yield_parity",
  ];

  it("puts the priority outcomes first, in the API's order", () => {
    const order = [
      "nitrate_leaching_reduction",
      "applied_n_reduction",
      "soil_carbon_change",
      "yield_parity",
    ];
    const ordered = orderOutcomes(decision(original), emphasis({ outcome_order: order }));
    expect(ordered.map((o) => o.outcome_id)).toEqual(order);
  });

  it("never drops an outcome, even one the API did not list", () => {
    const ordered = orderOutcomes(
      decision(original),
      emphasis({ outcome_order: ["applied_n_reduction"] }),
    );
    expect(ordered).toHaveLength(original.length);
    expect(ordered[0].outcome_id).toBe("applied_n_reduction");
    expect(new Set(ordered.map((o) => o.outcome_id))).toEqual(new Set(original));
  });

  it("keeps the engine's own order without an emphasis", () => {
    expect(orderOutcomes(decision(original), undefined).map((o) => o.outcome_id)).toEqual(
      original,
    );
  });

  it("does not change the decision it was given", () => {
    const d = decision(original);
    orderOutcomes(d, emphasis({ outcome_order: [...original].reverse() }));
    expect(d.outcomes.map((o) => o.outcome_id)).toEqual(original);
  });
});

describe("priorityGaps", () => {
  it("pairs each priority that applied with what we cannot tell the farmer about it", () => {
    const gaps = priorityGaps(
      emphasis({
        priorities_used: ["soil", "water"],
        gaps_for_priorities: [
          "Nothing here measures soil carbon or erosion on your field.",
          "Nothing here measures water leaving your soil.",
        ],
      }),
    );
    expect(gaps.map((g) => g.id)).toEqual(["soil", "water"]);
    expect(gaps[0]).toMatchObject({ label: "Look after the soil" });
    expect(gaps[0].gap).toContain("soil carbon");
    expect(gaps[1].gap).toContain("water leaving your soil");
  });

  it("is empty when no priority applied (all low, or none given)", () => {
    expect(priorityGaps(emphasis())).toEqual([]);
  });

  it("does not invent a gap when the API sent fewer gaps than priorities", () => {
    expect(
      priorityGaps(emphasis({ priorities_used: ["soil"], gaps_for_priorities: [] }))[0]
        .gap,
    ).toBe("");
  });
});
