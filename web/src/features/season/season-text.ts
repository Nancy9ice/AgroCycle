import type { SeasonIndicator, SeasonValue } from "./types";

const number = (value: number) =>
  new Intl.NumberFormat("en-GB", { maximumFractionDigits: 0 }).format(value);

/** "days", "spells", "mm", "degree-days C" read as a short phrase after a number. */
const unitWord = (unit: string) => (unit === "degree-days C" ? "degree-days" : unit);

/**
 * The plain sentence for one indicator: which past season was the highest and which the lowest. It states the
 * years, so the reader never has to work it out from colours. No claim about what the figure means for a crop.
 */
export function headline(indicator: SeasonIndicator): string {
  const { highest, lowest, unit } = indicator;
  if (!highest || !lowest) return "No season has a usable figure.";
  if (highest.year === lowest.year) {
    return `Only ${highest.year} has a figure: ${number(highest.value)} ${unitWord(unit)}.`;
  }
  return (
    `Highest in ${highest.year} (${number(highest.value)} ${unitWord(unit)}), ` +
    `lowest in ${lowest.year} (${number(lowest.value)} ${unitWord(unit)}).`
  );
}

/**
 * Bar heights as a percentage of the largest season. A season with no figure is `null`, never 0: an unknown
 * season must not look like a calm one. Known seasons get at least a sliver so a small value stays visible.
 */
export function barHeights(seasons: readonly SeasonValue[]): (number | null)[] {
  const known = seasons.flatMap((s) => (s.value === null ? [] : [s.value]));
  const max = known.length ? Math.max(...known) : 0;
  return seasons.map((s) =>
    s.value === null ? null : max <= 0 ? 4 : Math.max(4, (s.value / max) * 100),
  );
}

export const formatSeasonValue = number;
