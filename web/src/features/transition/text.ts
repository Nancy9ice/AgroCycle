import type { Readiness, TransitionStep } from "./types";

/** Year 0 is the step before the rotation starts; 1 and up are the rotation's years. */
export function stepHeading(step: TransitionStep): string {
  if (step.year === 0) return "Before you start: manure";
  return `Year ${step.year}: ${step.crop}`;
}

/** What the evidence behind a step is, in the reader's words. Nothing here is a validated agronomy claim. */
export function basisLabel(basis: TransitionStep["evidence_basis"]): string {
  switch (basis) {
    case "experimental":
      return "From the Marsden Farm experiment";
    case "team_proposed":
      return "The team’s own reading of the rotation, not reviewed by an agronomist";
    case "assumption":
      return "An assumption";
  }
}

/** The line shown for timing. Where no source gives it, it says so; it never offers a date. */
export function timingLine(step: TransitionStep): string {
  return step.timing_established
    ? step.timing_note
    : "Timing: not established. No source gives it, so we do not guess.";
}

export const readinessWord: Record<Readiness["status"], string> = {
  yes: "Yes",
  no: "No",
  not_answered: "Not answered",
};

/** Plain words for what an answer means for the step it bears on. A skipped answer is unknown, never "no". */
export function readinessNote(item: Readiness): string {
  if (item.status === "not_answered")
    return "You did not answer this, so we cannot say whether this step fits.";
  if (item.status === "yes") return "Nothing in your answer rules this step out.";
  return item.constraint === "manure_access"
    ? "Without manure, the nitrogen saving in the comparison does not apply."
    : "This step may not work for you as it stands. Talk to your adviser about it.";
}

export const strategyTabs = [
  { id: "B", label: "Switch to the three-year rotation (B)" },
  { id: "C", label: "Switch to the four-year rotation (C)" },
] as const;
