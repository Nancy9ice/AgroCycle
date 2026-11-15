import { describe, expect, it } from "vitest";
import { expectedCell, matchSentence, matchWord } from "./test-set-audit";
import type { ExpectationSummary } from "./get-test-set";

const summary = (overrides: Partial<ExpectationSummary> = {}): ExpectationSummary => ({
  cases_total: 135,
  cases_with_expectation: 4,
  cases_matching: 4,
  fields_with_expectation: 3,
  awaiting_review: 4,
  reviewed: 0,
  note: "n",
  ...overrides,
});

describe("expectedCell", () => {
  it("says plainly when there is no expectation, and does not invent one", () => {
    expect(expectedCell({ expected_outcome: null, expected_review_state: null })).toBe(
      "No expectation",
    );
  });

  it("marks an expectation that is still awaiting review, so it is not read as a benchmark", () => {
    expect(
      expectedCell({
        expected_outcome: "abstention",
        expected_review_state: "awaiting_review",
      }),
    ).toBe("We cannot compare these options for this field yet (awaiting review)");
  });

  it("does not add a review note once it has been reviewed", () => {
    expect(
      expectedCell({ expected_outcome: "abstention", expected_review_state: "reviewed" }),
    ).not.toContain("awaiting");
  });
});

describe("matchWord", () => {
  it("never shows a field with nothing to compare as a failure", () => {
    expect(matchWord(null)).toBe("No expectation");
    expect(matchWord(true)).toBe("Yes");
    expect(matchWord(false)).toBe("No");
  });
});

describe("matchSentence", () => {
  it("counts over the cases that have an expectation, not over all of them", () => {
    expect(matchSentence(summary())).toBe(
      "The engine matched the expectation in 4 of the 4 cases that have one.",
    );
  });

  it("reports a disagreement honestly", () => {
    expect(matchSentence(summary({ cases_matching: 3 }))).toContain("3 of the 4");
  });

  it("says there is nothing to match when no case has an expectation", () => {
    expect(matchSentence(summary({ cases_with_expectation: 0, cases_matching: 0 }))).toBe(
      "No case has an expectation, so there is nothing to match.",
    );
  });
});
