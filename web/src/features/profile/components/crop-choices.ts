/**
 * What a farmer can pick for each season, the quick starts, and the mapping from the profile's crop letters back to
 * form values. Plain data and functions, kept out of the client form so the server-rendered profile can use them too.
 */
export const FIRST_YEAR = 2015;
export const SEASONS = 11;

export const cropChoices = [
  { value: "corn", label: "Corn" },
  { value: "soybeans", label: "Soybeans" },
  { value: "oats", label: "Oats" },
  { value: "alfalfa", label: "Alfalfa" },
  { value: "pasture_hay", label: "Pasture or hay" },
  { value: "other", label: "Something else" },
] as const;

/** Shortcuts that fill the whole grid; the farmer can still change any season afterwards. */
export const presets: readonly { label: string; crops: readonly string[] }[] = [
  {
    label: "Corn and soybeans alternating, corn in 2025",
    crops: Array.from({ length: SEASONS }, (_, i) => (i % 2 === 0 ? "corn" : "soybeans")),
  },
  {
    label: "Corn and soybeans alternating, soybeans in 2025",
    crops: Array.from({ length: SEASONS }, (_, i) => (i % 2 === 0 ? "soybeans" : "corn")),
  },
  { label: "Corn every year", crops: Array(SEASONS).fill("corn") },
  { label: "Pasture or hay every year", crops: Array(SEASONS).fill("pasture_hay") },
];

/** The crop letters the profile uses, back to the form's values, so an answer can be edited. */
const LETTER_TO_CHOICE: Record<string, string> = {
  C: "corn",
  S: "soybeans",
  O: "oats",
  A: "alfalfa",
  G: "pasture_hay",
  X: "other",
};
export const choicesFromLetters = (letters: readonly string[]): string[] =>
  letters.map((letter) => LETTER_TO_CHOICE[letter] ?? "");
