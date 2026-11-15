import type { SeasonIndicator, SeasonThreshold, SeasonValue } from "./types";

const number = (value: number, decimals = 0) =>
  new Intl.NumberFormat("en-GB", { maximumFractionDigits: decimals }).format(value);

/** A temperature needs a decimal: 14.2 and 14.9 are not both "14". Everything else is shown whole. */
const decimalsFor = (unit: string) => (unit === "C" ? 1 : 0);

/** "days", "spells", "mm", "degree-days C", "C" read as a short phrase after a number. */
const unitWord = (unit: string) =>
  unit === "degree-days C" ? "degree-days" : unit === "C" ? "°C" : unit;

/**
 * The plain sentence for one indicator: which past season was the highest and which the lowest. It states the
 * years, so the reader never has to work it out from colours. No claim about what the figure means for a crop.
 */
export function headline(indicator: SeasonIndicator): string {
  const { highest, lowest, unit } = indicator;
  if (!highest || !lowest) return "No season has a usable figure.";
  if (highest.year === lowest.year) {
    return `Only ${highest.year} has a figure: ${number(highest.value, decimalsFor(unit))} ${unitWord(unit)}.`;
  }
  return (
    `Highest in ${highest.year} (${number(highest.value, decimalsFor(unit))} ${unitWord(unit)}), ` +
    `lowest in ${lowest.year} (${number(lowest.value, decimalsFor(unit))} ${unitWord(unit)}).`
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

export const formatSeasonValue = (value: number, unit = "") =>
  number(value, decimalsFor(unit));
export const unitLabel = unitWord;

/**
 * The threshold behind an indicator and how far to trust it, in one line. A count needs the line it is counted
 * against; a mean or a total has none, and says so. The basis and review status are always stated: a team-proposed
 * threshold is never presented as established.
 */
export function thresholdLine(threshold: SeasonThreshold): string {
  const line = threshold.threshold.toLowerCase().startsWith("none")
    ? "no threshold: it is a mean or a total, not a count"
    : // DS2's text sometimes already carries its unit (">= 10 days below 1 mm"); do not say "days" twice.
      threshold.threshold.toLowerCase().includes(threshold.unit.toLowerCase())
      ? threshold.threshold
      : `${threshold.threshold} ${threshold.unit}`.trim();
  const basis =
    threshold.evidence_basis === "team_proposed"
      ? "the team's own choice"
      : threshold.evidence_basis === "experimental"
        ? "from the experiment"
        : "an assumption";
  const review =
    threshold.review === "expert_reviewed"
      ? "reviewed by an agronomist"
      : "not reviewed by an agronomist";
  return `${line} (${basis}, ${review}).`;
}
