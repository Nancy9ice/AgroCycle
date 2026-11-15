import type { CoverMonth, CoverState, CoverYear } from "./types";

export const monthNames = [
  "Jan",
  "Feb",
  "Mar",
  "Apr",
  "May",
  "Jun",
  "Jul",
  "Aug",
  "Sep",
  "Oct",
  "Nov",
  "Dec",
] as const;

/** Short words for the cells. The state is written out, so it never depends on colour alone. */
export const stateWord: Record<CoverState, string> = {
  bare: "Bare",
  likely_bare: "Likely bare",
  green: "Green",
  unknown: "Unknown",
};

const plural = (n: number, word: string) => `${n} ${word}${n === 1 ? "" : "s"}`;

/**
 * One plain sentence per year. It counts months; it says nothing about what a bare or green month means for a
 * crop, because the images cannot say that.
 */
export function yearSummary(year: CoverYear): string {
  const known = plural(year.months_with_images, "month");
  const bare =
    year.bare_months === 0
      ? "No month looked bare"
      : `${plural(year.bare_months, "month")} bare or likely bare`;
  return `${year.year}: ${bare}. ${known} had enough images to say.`;
}

/** The accessible name of one cell. */
export function cellLabel(year: number, month: CoverMonth): string {
  const images =
    month.usable_images === 0
      ? "no usable image"
      : `${plural(month.usable_images, "usable image")}`;
  return `${monthNames[month.month - 1]} ${year}: ${stateWord[month.state].toLowerCase()}, ${images}`;
}
