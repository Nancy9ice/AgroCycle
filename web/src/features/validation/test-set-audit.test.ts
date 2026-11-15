import { describe, expect, it } from "vitest";
import { expectationNote } from "./test-set-audit";

describe("expectationNote", () => {
  it("names DS1's handover and the run, and says it is not correctness", () => {
    const text = expectationNote({
      expected_source: "ds1_expected",
      expected_basis: "run ds1_handover, rules 2026-11-14.1",
    });
    expect(text).toContain("DS1’s handover");
    expect(text).toContain("run ds1_handover, rules 2026-11-14.1");
    expect(text).toMatch(/consistency, not correctness/);
  });

  it("is honest when the expectation was derived by the team instead", () => {
    const text = expectationNote({
      expected_source: "selection_label",
      expected_basis: "",
    });
    expect(text).toMatch(/ourselves from how each field was chosen/);
    expect(text).not.toContain("DS1");
  });

  it("says when it is a mix", () => {
    const text = expectationNote({
      expected_source: "mixed",
      expected_basis: "run r1, rules v1",
    });
    expect(text).toMatch(/for most fields/);
    expect(text).toContain("run r1, rules v1");
  });
});
