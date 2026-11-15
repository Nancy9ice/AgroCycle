/**
 * Plain wording for what the engine says. DS2's rule text stays as written in `engine/`; this is the layer
 * between it and a farmer. It only rewrites how a sentence is said: it never adds, removes or softens a
 * claim, and a sentence it does not know passes through unchanged, so a newer engine version cannot
 * lose text because of it.
 */

/** Whole sentences the engine uses often, in the words a farmer would use. */
const sentences: ReadonlyMap<string, string> = new Map([
  [
    "One or more required profile indicators came back unknown.",
    "At least one of the weather or soil measurements this field needs is missing.",
  ],
  [
    "The climate comparison with the Marsden site could not be computed.",
    "We could not compare this field’s growing season with the Iowa trial farm’s, because the weather data is missing.",
  ],
  [
    "Climate indicators are POWER grid values, about 50 km across, not field measurements.",
    "Weather figures are for an area about 50 km across, not measured on your field.",
  ],
  [
    "Soil values come from a mapped survey, not from sampling this field.",
    "Soil figures come from soil maps, not from a test on this field.",
  ],
  [
    "Every applicability rule is a team-proposed guardrail and is not expert-reviewed.",
    "The rules that decide which options fit your farm were written by our team. No expert has checked them yet.",
  ],
  [
    "No profitability is calculated; the data PRD 9 requires for it is not available.",
    "We do not work out profit. That would need your own costs, yields and prices, which we do not have.",
  ],
]);

/** Matches "PRD section 7.4", "PRD sections 7.4 and 4.4" and "PRD 9". */
const prdReference = /PRD (?:sections? )?\d+(?:\.\d+)*(?: and \d+(?:\.\d+)*)?/g;

const matchCase = (word: string, replacement: string) =>
  word[0] === word[0].toUpperCase()
    ? replacement[0].toUpperCase() + replacement.slice(1)
    : replacement;

export function plain(text: string): string {
  const known = sentences.get(text.trim());
  if (known) return known;
  return text
    .replace(/\s*\((?:[^()]*; )?PRD (?:sections? )?[\d.]+(?: and [\d.]+)?\)/g, "")
    .replace(/;\s*AgroCycle scope\s*$/, "")
    .replace(prdReference, "AgroCycle’s own scope notes")
    .replace(/\bmaize\b/gi, (word) => matchCase(word, "corn"));
}

export const plainAll = (texts: readonly string[]): string[] => texts.map(plain);
