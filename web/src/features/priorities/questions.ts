/**
 * The questions on the priorities screen (PRD §5.2 step 6, §9).
 *
 * Constraints are written to match DS2's applicability rules: the ones with an `engineKey` are
 * read by the engine (`docs/rules/strategy-profiles-and-applicability.md`); the rest are captured
 * for the adviser summary and tagged as such, so the form never implies an effect that does not
 * exist. Every question is optional, and "unanswered" is a first-class state.
 */

export interface QuestionOption {
  value: string;
  label: string;
}

export type EngineKey =
  | "manure_access"
  | "forage_use_or_buyer"
  | "oat_use_or_buyer"
  | "small_grain_equipment_or_contractor";

export interface Question {
  id: string;
  group: "priority" | "constraint";
  label: string;
  /** Why we ask, in plain language. Shown under constraint questions. */
  why?: string;
  options: readonly QuestionOption[];
  /** The engine context key this answer feeds, if any. */
  engineKey?: EngineKey;
  /** Option values that mean "yes" (`true`) or "no" (`false`) to the engine. Anything else is unknown. */
  yes?: readonly string[];
  no?: readonly string[];
}

const levels: readonly QuestionOption[] = [
  { value: "low", label: "Low" },
  { value: "medium", label: "Medium" },
  { value: "high", label: "High" },
];

export const questions = [
  // What matters (PRD §3, §9: soil health, water, input use, income diversification, forage)
  { id: "soil", group: "priority", label: "Look after the soil", options: levels },
  {
    id: "water",
    group: "priority",
    label: "Cope better with dry or wet years",
    options: levels,
  },
  {
    id: "inputs",
    group: "priority",
    label: "Spend less on fertiliser and weed-killer",
    options: levels,
  },
  {
    id: "income",
    group: "priority",
    label: "Earn from more than two crops",
    options: levels,
  },
  {
    id: "forage",
    group: "priority",
    label: "Grow hay or feed for animals",
    options: levels,
  },

  // What is possible
  {
    id: "manure",
    group: "constraint",
    label: "Can you get manure for this field?",
    why: "In the Iowa trial, part of the fertiliser savings came from manure. Without manure, that comparison may not apply to you. If you only have a little, choose “Not sure” and ask your adviser.",
    options: [
      { value: "yes", label: "Yes" },
      { value: "no", label: "No" },
      { value: "unsure", label: "Not sure" },
    ],
    engineKey: "manure_access",
    yes: ["yes"],
    no: ["no"],
  },
  {
    id: "hayOutlet",
    group: "constraint",
    label: "Do you keep animals, or know someone who would buy hay?",
    why: "The four-year option grows alfalfa for two years in four, and hay needs somewhere to go.",
    options: [
      { value: "own_livestock", label: "I keep animals" },
      { value: "can_sell", label: "I could sell hay" },
      { value: "neither", label: "Neither" },
      { value: "unsure", label: "Not sure" },
    ],
    engineKey: "forage_use_or_buyer",
    yes: ["own_livestock", "can_sell"],
    no: ["neither"],
  },
  {
    id: "oatOutlet",
    group: "constraint",
    label: "Somewhere to use or sell oats and oat straw?",
    why: "Both longer options include an oat year. A new crop is only useful if it can be used or sold.",
    options: [
      { value: "yes", label: "Yes" },
      { value: "some", label: "Some" },
      { value: "none", label: "None" },
      { value: "unsure", label: "Not sure" },
    ],
    engineKey: "oat_use_or_buyer",
    yes: ["yes", "some"],
    no: ["none"],
  },
  {
    id: "grainEquipment",
    group: "constraint",
    label: "Equipment, or a contractor, to plant and harvest oats",
    why: "Both longer options include an oat year, which needs small-grain equipment and labour.",
    options: [
      { value: "have", label: "I have it" },
      { value: "can_hire", label: "I can hire it" },
      { value: "no", label: "No" },
      { value: "unsure", label: "Not sure" },
    ],
    engineKey: "small_grain_equipment_or_contractor",
    yes: ["have", "can_hire"],
    no: ["no"],
  },
  {
    id: "hayEquipment",
    group: "constraint",
    label: "Equipment, or a contractor, to cut and bale hay",
    why: "Red clover and alfalfa are usually cut for hay.",
    options: [
      { value: "have", label: "I have it" },
      { value: "can_hire", label: "I can hire it" },
      { value: "no", label: "No" },
      { value: "unsure", label: "Not sure" },
    ],
  },
  {
    id: "storage",
    group: "constraint",
    label: "Space to store hay or grain",
    why: "Hay usually has to be stored before it is sold.",
    options: [
      { value: "yes", label: "Yes" },
      { value: "no", label: "No" },
      { value: "unsure", label: "Not sure" },
    ],
  },
  {
    id: "labour",
    group: "constraint",
    label: "Extra help at busy times",
    why: "Longer rotations mean more jobs spread across the year.",
    options: [
      { value: "little", label: "Little" },
      { value: "some", label: "Some" },
      { value: "plenty", label: "Plenty" },
    ],
  },
] as const satisfies readonly Question[];

export type QuestionId = (typeof questions)[number]["id"];

export const priorityQuestions = questions.filter((q) => q.group === "priority");
export const constraintQuestions = questions.filter((q) => q.group === "constraint");

/** Answers by question id. A missing key means the question was not answered. */
export type Answers = Partial<Record<QuestionId, string>>;

export const TOTAL_QUESTIONS = questions.length;

export function optionLabel(
  question: Question,
  value: string | undefined,
): string | null {
  return question.options.find((option) => option.value === value)?.label ?? null;
}
