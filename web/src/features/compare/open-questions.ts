import { questions, type EngineKey } from "@/features/priorities/questions";

export interface OpenQuestion {
  key: string;
  text: string;
  /** `you` can be answered on the priorities screen; `data` needs a data source we do not have yet. */
  kind: "you" | "data";
  /** The priorities-form question to jump back to, for `you` items. */
  questionId?: string;
}

const dataLabels: Readonly<Record<string, string>> = {
  county: "Which county the field is in",
  crop_history_is_maize_soybean:
    "Whether this field's recent crops follow a maize–soybean rotation",
  gdd_season_difference_vs_marsden:
    "How this field's growing-season warmth compares with the Iowa trial site",
  frost_free_days: "How many frost-free days this field usually has",
  dominant_drainage_class: "How well the soil drains (missing for this field)",
  "indicator gdd": "Growing-season heat accumulation (growing degree days)",
  "indicator precipitation_total": "Growing-season rainfall total",
  "indicator frost_window": "The frost-free window",
  "indicator om_r_0_30cm":
    "Soil organic matter in the top 30 cm (missing, or covering only part of this field)",
};

const engineKeys = new Set<string>([
  "manure_access",
  "forage_use_or_buyer",
  "oat_use_or_buyer",
  "small_grain_equipment_or_contractor",
] satisfies EngineKey[]);

/** Turns the engine's unknowns into questions a person can act on. Unmapped keys stay visible as-is. */
export function toOpenQuestions(unknowns: readonly string[]): OpenQuestion[] {
  return unknowns.map((key): OpenQuestion => {
    if (engineKeys.has(key)) {
      const question = questions.find((q) => "engineKey" in q && q.engineKey === key);
      return {
        key,
        kind: "you",
        text: question?.label ?? key,
        questionId: question?.id,
      };
    }
    return { key, kind: "data", text: dataLabels[key] ?? key };
  });
}
