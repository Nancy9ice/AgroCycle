import { crops, isCropCode, type CropCode } from "@/domain/crops";
import type { CropHistory, CropYear } from "./types";

/** Turns DE's "SCSCSCSCSCS" string into one entry per year. */
export function parseCropSequence(sequence: string, firstYear: number): CropYear[] {
  return [...sequence].map((letter, index) => {
    if (!isCropCode(letter))
      throw new Error(`Unknown crop code "${letter}" in "${sequence}"`);
    return { year: firstYear + index, code: letter };
  });
}

/**
 * A corn and soybean history counts as "mostly alternating" when at most this many years repeat
 * the previous year's crop (2 of 10 year-to-year changes). More repeats read as a mix.
 */
const MAX_REPEATS_FOR_ALTERNATING = 2;

const label = (code: CropCode) => crops[code].label;
const lower = (code: CropCode) => label(code).toLowerCase();

function joinList(items: readonly string[]): string {
  if (items.length <= 1) return items.join("");
  return `${items.slice(0, -1).join(", ")} and ${items[items.length - 1]}`;
}

/**
 * Describes the crop sequence in one honest sentence, using only what the sequence shows.
 * This stands in for the API: the UI renders the sentence and never writes its own.
 */
export function buildCropHistory(sequence: string, firstYear: number): CropHistory {
  const years = parseCropSequence(sequence, firstYear);
  const first = years[0].year;
  const last = years[years.length - 1].year;
  const span = `${first} to ${last}`;
  const distinct = [...new Set(years.map((y) => y.code))];

  const repeatedYears = years
    .filter((entry, index) => index > 0 && entry.code === years[index - 1].code)
    .map((entry) => entry.year);

  let summary: string;
  if (distinct.length === 1) {
    summary = `${label(distinct[0])} in every year, ${span}.`;
  } else if (
    distinct.every((code) => code === "C" || code === "S") &&
    repeatedYears.length <= MAX_REPEATS_FOR_ALTERNATING
  ) {
    if (repeatedYears.length === 0) {
      summary = `Corn and soybeans alternate every year, ${span}: the pattern AgroCycle is built for.`;
    } else {
      const repeats = repeatedYears.map((year) => years.find((y) => y.year === year)!);
      const named = repeats.map((entry) => `${lower(entry.code)} in ${entry.year}`);
      summary = `Corn and soybeans, mostly alternating, ${span}. A crop repeats in ${repeatedYears.length === 1 ? "one year" : `${repeatedYears.length} years`}: ${joinList(named)}.`;
    }
  } else {
    const counts = distinct
      .map((code) => ({ code, n: years.filter((y) => y.code === code).length }))
      .sort((a, b) => b.n - a.n);
    summary = `A mix of crops, ${span}: ${counts.map(({ code, n }) => `${lower(code)} ${n} ${n === 1 ? "year" : "years"}`).join(", ")}.`;
  }

  return { years, summary, repeatedYears };
}
