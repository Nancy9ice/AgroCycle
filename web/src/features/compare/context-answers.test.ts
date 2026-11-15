import { describe, expect, it } from "vitest";
import { hasContext, toContextAnswers } from "./engine-input";

describe("toContextAnswers", () => {
  it("reads nothing into an unanswered form: everything is unknown, never 'no'", () => {
    expect(toContextAnswers({})).toEqual({
      hay_equipment_or_contractor: null,
      storage_space: null,
      extra_labour: null,
    });
    expect(hasContext(toContextAnswers({}))).toBe(false);
  });

  it.each([
    ["have", true],
    ["can_hire", true],
    ["no", false],
    ["unsure", null],
  ])("hay equipment %s becomes %s", (answer, expected) => {
    expect(toContextAnswers({ hayEquipment: answer }).hay_equipment_or_contractor).toBe(
      expected,
    );
  });

  it("maps storage yes and no, and treats 'not sure' as unknown", () => {
    expect(toContextAnswers({ storage: "yes" }).storage_space).toBe(true);
    expect(toContextAnswers({ storage: "no" }).storage_space).toBe(false);
    expect(toContextAnswers({ storage: "unsure" }).storage_space).toBeNull();
  });

  it("passes labour through and rejects anything else", () => {
    expect(toContextAnswers({ labour: "some" }).extra_labour).toBe("some");
    expect(toContextAnswers({ labour: "lots" }).extra_labour).toBeNull();
    expect(hasContext(toContextAnswers({ labour: "little" }))).toBe(true);
  });
});
