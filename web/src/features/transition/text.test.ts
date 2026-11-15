import { describe, expect, it } from "vitest";
import {
  basisLabel,
  readinessNote,
  readinessWord,
  stepHeading,
  timingLine,
} from "./text";
import type { Readiness, TransitionStep } from "./types";

const step = (overrides: Partial<TransitionStep> = {}): TransitionStep => ({
  year: 1,
  crop: "corn",
  action: "Grow corn.",
  needs: [],
  timing_note: "not established: no source gives timing for this phase",
  timing_established: false,
  evidence_basis: "experimental",
  source: "s",
  shows_past_weather: true,
  ...overrides,
});

const readiness = (overrides: Partial<Readiness> = {}): Readiness => ({
  constraint: "oat_use_or_buyer",
  label: "l",
  answer: null,
  status: "not_answered",
  step_year: 3,
  ...overrides,
});

describe("stepHeading", () => {
  it("calls year 0 the step before the rotation starts, and numbers the rest", () => {
    expect(stepHeading(step({ year: 0, crop: "manure" }))).toBe(
      "Before you start: manure",
    );
    expect(stepHeading(step({ year: 3, crop: "oat with red clover" }))).toBe(
      "Year 3: oat with red clover",
    );
  });
});

describe("timingLine", () => {
  it("says timing is not established, and offers no date, when no source gives it", () => {
    const text = timingLine(step());
    expect(text).toBe("Timing: not established. No source gives it, so we do not guess.");
    expect(text).not.toMatch(/\d/);
  });

  it("shows the sourced timing when there is one", () => {
    expect(
      timingLine(
        step({
          timing_established: true,
          timing_note: "Applied in October of each year (Text S1).",
        }),
      ),
    ).toContain("October");
  });
});

describe("basisLabel", () => {
  it("never presents the team's own reading as established or reviewed", () => {
    expect(basisLabel("team_proposed")).toMatch(/not reviewed by an agronomist/);
    expect(basisLabel("experimental")).toMatch(/Marsden Farm experiment/);
    expect(basisLabel("assumption")).toMatch(/assumption/i);
  });
});

describe("readiness", () => {
  it("treats a skipped answer as unknown, never as no", () => {
    expect(readinessWord.not_answered).toBe("Not answered");
    expect(readinessNote(readiness())).toMatch(/did not answer.*cannot say/);
  });

  it("says plainly what no manure means for the comparison", () => {
    const note = readinessNote(
      readiness({ constraint: "manure_access", status: "no", answer: false }),
    );
    expect(note).toBe(
      "Without manure, the nitrogen saving in the comparison does not apply.",
    );
  });

  it("does not claim a yes makes the step certain", () => {
    expect(readinessNote(readiness({ status: "yes", answer: true }))).toBe(
      "Nothing in your answer rules this step out.",
    );
  });

  it("points a no on any other step at the adviser rather than inventing a consequence", () => {
    expect(readinessNote(readiness({ status: "no", answer: false }))).toMatch(/adviser/);
  });
});
