import { describe, expect, it } from "vitest";
import { barHeights, formatSeasonValue, headline, thresholdLine } from "./season-text";
import type { SeasonIndicator, SeasonThreshold, SeasonValue } from "./types";

const season = (year: number, value: number | null): SeasonValue => ({
  year,
  value,
  status: value === null ? "unknown" : "available",
  window_start: `${year}-04-01`,
  window_end: `${year}-10-31`,
  unknown_reason: "",
});

const indicator = (overrides: Partial<SeasonIndicator> = {}): SeasonIndicator => ({
  indicator_id: "heat_days",
  label: "Very hot days (30 °C or more)",
  unit: "days",
  evidence_type: "model_reanalysis",
  scale: "grid",
  source: "NASA POWER",
  formula: "f",
  limitation: "l",
  threshold: null,
  seasons: [season(2019, 9), season(2021, 73)],
  seasons_used: 2,
  seasons_total: 2,
  highest: { year: 2021, value: 73 },
  lowest: { year: 2019, value: 9 },
  ...overrides,
});

describe("headline", () => {
  it("names the highest and the lowest season with their years and units", () => {
    expect(headline(indicator())).toBe(
      "Highest in 2021 (73 days), lowest in 2019 (9 days).",
    );
  });

  it("writes degree-days as a phrase and rounds long values", () => {
    const text = headline(
      indicator({
        unit: "degree-days C",
        highest: { year: 2023, value: 2144.085 },
        lowest: { year: 2019, value: 1773.47 },
      }),
    );
    expect(text).toBe(
      "Highest in 2023 (2,144 degree-days), lowest in 2019 (1,773 degree-days).",
    );
  });

  it("does not invent a contrast when only one season has a figure", () => {
    const text = headline(
      indicator({
        highest: { year: 2015, value: 12 },
        lowest: { year: 2015, value: 12 },
      }),
    );
    expect(text).toBe("Only 2015 has a figure: 12 days.");
  });

  it("says plainly when no season has a figure", () => {
    expect(headline(indicator({ highest: null, lowest: null }))).toBe(
      "No season has a usable figure.",
    );
  });

  it("makes no claim about what the figure means for a crop", () => {
    expect(headline(indicator()).toLowerCase()).not.toMatch(
      /yield|stress|loss|risk|good|bad/,
    );
  });
});

describe("barHeights", () => {
  it("scales to the largest season", () => {
    expect(barHeights([season(1, 50), season(2, 100)])).toEqual([50, 100]);
  });

  it("never turns an unknown season into a zero-height bar", () => {
    expect(barHeights([season(1, null), season(2, 10)])).toEqual([null, 100]);
  });

  it("keeps a small known value visible", () => {
    const [small, big] = barHeights([season(1, 1), season(2, 1000)]);
    expect(small).toBeGreaterThanOrEqual(4);
    expect(big).toBe(100);
  });

  it("copes with all-zero and all-unknown seasons", () => {
    expect(barHeights([season(1, 0), season(2, 0)])).toEqual([4, 4]);
    expect(barHeights([season(1, null)])).toEqual([null]);
  });
});

describe("temperature and the threshold line", () => {
  it("shows a temperature to one decimal and in degrees, never as 14 C", () => {
    const text = headline(
      indicator({
        unit: "C",
        highest: { year: 2021, value: 14.94 },
        lowest: { year: 2019, value: 13.21 },
      }),
    );
    expect(text).toBe("Highest in 2021 (14.9 °C), lowest in 2019 (13.2 °C).");
    expect(formatSeasonValue(14.94, "C")).toBe("14.9");
    expect(formatSeasonValue(73.4, "days")).toBe("73"); // everything else stays whole
  });

  const threshold = (overrides: Partial<SeasonThreshold> = {}): SeasonThreshold => ({
    what_it_counts: "Days the daily maximum reached the threshold or more",
    threshold: ">= 30",
    unit: "degrees C",
    evidence_basis: "team_proposed",
    review: "not_expert_reviewed",
    limitation: "l",
    code_version: "v",
    ...overrides,
  });

  it("states the line, whose choice it was, and that no agronomist reviewed it", () => {
    expect(thresholdLine(threshold())).toBe(
      ">= 30 degrees C (the team's own choice, not reviewed by an agronomist).",
    );
  });

  it("does not repeat a unit the threshold text already carries", () => {
    const line = thresholdLine(
      threshold({ threshold: ">= 10 days below 1 mm", unit: "days" }),
    );
    expect(line).toBe(
      ">= 10 days below 1 mm (the team's own choice, not reviewed by an agronomist).",
    );
    expect(
      thresholdLine(threshold({ threshold: "base 10, cap 30", unit: "degrees C" })),
    ).toContain("cap 30 degrees C");
  });

  it("says a mean or a total has no threshold, instead of printing 'none: a total'", () => {
    const line = thresholdLine(
      threshold({ threshold: "none: a total, not a count", unit: "mm" }),
    );
    expect(line).toBe(
      "no threshold: it is a mean or a total, not a count (the team's own choice, not reviewed by an agronomist).",
    );
  });

  it("only says reviewed when DS2's table says so", () => {
    expect(thresholdLine(threshold({ review: "expert_reviewed" }))).toContain(
      "reviewed by an agronomist",
    );
    expect(thresholdLine(threshold({ review: "expert_reviewed" }))).not.toContain(
      "not reviewed",
    );
  });
});
