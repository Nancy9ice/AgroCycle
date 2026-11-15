import { describe, expect, it } from "vitest";
import { countAnswered, parseAnswers, serializeAnswers } from "./answers-codec";
import { toEngineContext } from "./engine-context";
import {
  constraintQuestions,
  priorityQuestions,
  questions,
  startingPointAnswers,
  TOTAL_QUESTIONS,
  type Answers,
} from "./questions";

describe("question set", () => {
  it("has 5 priorities and 7 constraints, 12 in all, with unique ids", () => {
    expect(questions.filter((q) => q.group === "priority")).toHaveLength(5);
    expect(questions.filter((q) => q.group === "constraint")).toHaveLength(7);
    expect(TOTAL_QUESTIONS).toBe(12);
    expect(new Set(questions.map((q) => q.id)).size).toBe(12);
  });

  it("feeds exactly the four context keys DS2's rules read", () => {
    const keys = questions.flatMap((q) => ("engineKey" in q ? [q.engineKey] : [])).sort();
    expect(keys).toEqual([
      "forage_use_or_buyer",
      "manure_access",
      "oat_use_or_buyer",
      "small_grain_equipment_or_contractor",
    ]);
  });

  it("only uses option values that exist in each yes/no list", () => {
    for (const q of questions) {
      if (!("engineKey" in q)) continue;
      const values = q.options.map((o) => o.value as string);
      for (const v of [...q.yes, ...q.no] as string[]) expect(values).toContain(v);
      // "Not sure" must never be a yes or a no.
      expect([...q.yes, ...q.no] as string[]).not.toContain("unsure");
    }
  });
});

describe("toEngineContext", () => {
  it("treats everything unanswered as unknown, never as yes", () => {
    expect(toEngineContext({})).toEqual({
      manure_access: null,
      forage_use_or_buyer: null,
      oat_use_or_buyer: null,
      small_grain_equipment_or_contractor: null,
    });
  });

  it.each([
    ["manure", "yes", "manure_access", true],
    ["manure", "no", "manure_access", false],
    ["manure", "unsure", "manure_access", null],
    ["hayOutlet", "own_livestock", "forage_use_or_buyer", true],
    ["hayOutlet", "can_sell", "forage_use_or_buyer", true],
    ["hayOutlet", "neither", "forage_use_or_buyer", false],
    ["hayOutlet", "unsure", "forage_use_or_buyer", null],
    ["oatOutlet", "yes", "oat_use_or_buyer", true],
    ["oatOutlet", "some", "oat_use_or_buyer", true],
    ["oatOutlet", "none", "oat_use_or_buyer", false],
    ["oatOutlet", "unsure", "oat_use_or_buyer", null],
    ["grainEquipment", "have", "small_grain_equipment_or_contractor", true],
    ["grainEquipment", "can_hire", "small_grain_equipment_or_contractor", true],
    ["grainEquipment", "no", "small_grain_equipment_or_contractor", false],
    ["grainEquipment", "unsure", "small_grain_equipment_or_contractor", null],
  ] as const)("%s = %s sets %s to %s", (id, value, key, expected) => {
    expect(toEngineContext({ [id]: value } as Answers)[key]).toBe(expected);
  });

  it("ignores priorities and the recorded-only constraints", () => {
    const answers: Answers = {
      soil: "high",
      hayEquipment: "no",
      storage: "no",
      labour: "little",
    };
    expect(toEngineContext(answers)).toEqual(toEngineContext({}));
  });
});

describe("answers codec", () => {
  it("round-trips answers through the URL", () => {
    const answers: Answers = { soil: "high", manure: "no", labour: "some" };
    const params = serializeAnswers(answers);
    expect(params.toString()).toBe("soil=high&manure=no&labour=some");
    expect(parseAnswers(params)).toEqual(answers);
  });

  it("omits unanswered questions", () => {
    expect(serializeAnswers({}).toString()).toBe("");
  });

  it("drops unknown keys and unknown values from a hand-edited URL", () => {
    const params = new URLSearchParams(
      "soil=extreme&manure=yes&evil=<script>&hayOutlet=can_sell",
    );
    expect(parseAnswers(params)).toEqual({ manure: "yes", hayOutlet: "can_sell" });
  });

  it("keeps the first of a repeated key", () => {
    expect(parseAnswers(new URLSearchParams("manure=no&manure=yes"))).toEqual({
      manure: "no",
    });
  });

  it("counts answered questions", () => {
    expect(countAnswered({})).toBe(0);
    expect(countAnswered({ soil: "low", manure: "unsure" })).toBe(2);
  });
});

describe("startingPointAnswers", () => {
  const start = startingPointAnswers();

  it("sets every priority to medium", () => {
    for (const question of priorityQuestions) expect(start[question.id]).toBe("medium");
  });

  it("never answers yes or no about the farm", () => {
    for (const question of constraintQuestions) {
      const value = start[question.id];
      if (value === undefined) continue;
      expect(value).toBe("unsure");
    }
  });

  it("leaves a question without a Not sure option unanswered", () => {
    expect(start.labour).toBeUndefined();
  });

  it("reaches the engine as unknown, never as a yes or a no", () => {
    const context = toEngineContext(start);
    for (const value of Object.values(context)) expect(value).toBeNull();
  });

  it("survives the URL round trip", () => {
    expect(parseAnswers(serializeAnswers(start))).toEqual(start);
  });
});
