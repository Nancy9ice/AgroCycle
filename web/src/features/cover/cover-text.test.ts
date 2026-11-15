import { describe, expect, it } from "vitest";
import { cellLabel, monthNames, stateWord, yearSummary } from "./cover-text";
import type { CoverMonth, CoverYear } from "./types";

const month = (overrides: Partial<CoverMonth> = {}): CoverMonth => ({
  month: 6,
  state: "green",
  usable_images: 3,
  bare_days: 0,
  days: 30,
  ...overrides,
});

const year = (overrides: Partial<CoverYear> = {}): CoverYear => ({
  year: 2024,
  months: [],
  bare_months: 0,
  months_with_images: 7,
  ...overrides,
});

describe("yearSummary", () => {
  it("counts months and says nothing about what they mean for a crop", () => {
    const text = yearSummary(year({ bare_months: 2 }));
    expect(text).toBe(
      "2024: 2 months bare or likely bare. 7 months had enough images to say.",
    );
    expect(text.toLowerCase()).not.toMatch(/yield|crop|stress|risk|erosion/);
  });

  it("says plainly when nothing looked bare, and uses singular words for one", () => {
    expect(yearSummary(year({ bare_months: 0, months_with_images: 1 }))).toBe(
      "2024: No month looked bare. 1 month had enough images to say.",
    );
    expect(yearSummary(year({ bare_months: 1 }))).toContain(
      "1 month bare or likely bare",
    );
  });
});

describe("cell text", () => {
  it("writes every state out in words, so colour is never the only signal", () => {
    expect(Object.values(stateWord)).toEqual(["Bare", "Likely bare", "Green", "Unknown"]);
  });

  it("names the month, the state and how many images stand behind it", () => {
    expect(cellLabel(2024, month())).toBe("Jun 2024: green, 3 usable images");
    expect(
      cellLabel(2025, month({ month: 1, state: "likely_bare", usable_images: 0 })),
    ).toBe("Jan 2025: likely bare, no usable image");
    expect(cellLabel(2024, month({ usable_images: 1, state: "unknown" }))).toBe(
      "Jun 2024: unknown, 1 usable image",
    );
  });

  it("has twelve month names, January first", () => {
    expect(monthNames).toHaveLength(12);
    expect(monthNames[0]).toBe("Jan");
    expect(monthNames[11]).toBe("Dec");
  });
});
