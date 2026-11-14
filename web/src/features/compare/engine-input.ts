import type { DemoField } from "@/features/field/types";
import type { FieldProfile } from "@/features/profile/types";
import type { Answers } from "@/features/priorities/questions";
import { toEngineContext } from "@/features/priorities/engine-context";
import type { EngineConstraints, EngineProfile } from "./evaluate";
import { ruleTable } from "./rules";

/**
 * Values used only by the optional sample preview (`?preview=sample`). They are NOT this field's
 * data: no required indicator is computed for any field yet (roadmap Phases 4 and 5), so without
 * the preview the real engine abstains. The preview exists so the other two outcomes can be seen
 * and the screen can be reviewed; the page says so wherever it is used.
 */
const SAMPLE = { gddDifference: 120, frostFreeDays: 150 } as const;

/**
 * Maps a field and its profile onto the engine's inputs.
 *
 * Only facts the data layer already decided go in: the field's class (`rotation` is DE's
 * "in-domain: maize-soybean rotation"), its county and its boundary source. Everything the
 * pipeline cannot supply yet is `null` (unknown), never a guess.
 */
export function toEngineProfile(
  field: DemoField,
  profile: FieldProfile,
  options: { sample: boolean },
): EngineProfile {
  const indicatorStatuses = options.sample
    ? Object.fromEntries(ruleTable.requiredIndicators.map((id) => [id, "ok"]))
    : {};
  return {
    field_id: field.id,
    boundary_source: field.boundarySource,
    crop_history_summary: profile.cropHistory.data?.summary ?? "Crop history not loaded.",
    county: field.county,
    crop_history_is_maize_soybean: field.fieldClass === "rotation",
    gdd_season_difference_vs_marsden: options.sample ? SAMPLE.gddDifference : null,
    frost_free_days: options.sample ? SAMPLE.frostFreeDays : null,
    // Drainage is not loaded yet (the soil section says so), so it stays unknown.
    dominant_drainage_class: null,
    indicator_statuses: indicatorStatuses,
  };
}

/** Answers become the engine's four nullable booleans; "high" priorities are passed along as recorded. */
export function toEngineConstraints(answers: Answers): EngineConstraints {
  const priorities = Object.entries(answers)
    .filter(([id, value]) => value === "high" && PRIORITY_IDS.includes(id))
    .map(([id]) => id);
  return { ...toEngineContext(answers), priorities };
}

const PRIORITY_IDS = ["soil", "water", "inputs", "income", "forage"];
