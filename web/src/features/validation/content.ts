/**
 * What has been checked, and how. Written by hand from the repo's own records (each spec's
 * `validation.md` and the roadmap tracker) as of `SNAPSHOT_DATE`. Nothing here is computed or
 * rounded up: a check that is not recorded in a spec is "not done". Update this file, and the date,
 * whenever a Phase 14 result lands. A row moves to "done" only when a spec result says so.
 */

export const SNAPSHOT_DATE = "14 November 2026";

export type CheckKind = "internal" | "otherSource" | "independent" | "expert";
export type CheckState = "done" | "partly" | "none";

/** PRD §11: these four must never be merged, and "validated" must not stand for the first. */
export const checkKinds: readonly {
  id: CheckKind;
  label: string;
  meaning: string;
}[] = [
  {
    id: "internal",
    label: "Our own tests",
    meaning:
      "Tests we wrote check that the code does what we meant. They show it is consistent, not that it is right about the real world.",
  },
  {
    id: "otherSource",
    label: "Compared with another source",
    meaning:
      "Our output set beside a paper or a different data product. Agreement is encouraging, but both may share the same mistakes, so it is not independent proof.",
  },
  {
    id: "independent",
    label: "Checked against an independent reference",
    meaning:
      "Our output checked against a separate reference, such as crops recorded on the ground. This is the only kind that shows accuracy.",
  },
  {
    id: "expert",
    label: "Reviewed by an expert",
    meaning:
      "A farmer or adviser who knows the area has read it and said whether it makes sense.",
  },
];

export interface ValidationRow {
  id: string;
  component: string;
  /** What was checked. */
  checked: string;
  /** The result as recorded. */
  result: string;
  /** What the checks do not show. */
  doesNotShow: string;
  /** Where the record lives in the repository. */
  source: string;
  kinds: Readonly<Record<CheckKind, CheckState>>;
}

const none: Record<CheckKind, CheckState> = {
  internal: "none",
  otherSource: "none",
  independent: "none",
  expert: "none",
};

export const validationRows: readonly ValidationRow[] = [
  {
    id: "geometry",
    component: "Field boundaries",
    checked:
      "Each demonstration polygon is checked for a closed outline, at least four points, no self-crossing, and a position inside Story or Boone County. The app and the data team's validator both run these checks.",
    result:
      "All 45 demonstration fields pass. The app's geometry tests include all 45, and the data validator reports “OK: 45 fields valid”.",
    doesNotShow:
      "All 45 boundaries are demonstration polygons drawn by the team, not real farms, so how real boundaries behave is unknown. Drawing or uploading a boundary is not built yet.",
    source:
      "specs/features/2026-11-14-fe-field-selection; specs/features/2026-11-14-de-repo-infra-and-fields",
    kinds: { ...none, internal: "done" },
  },
  {
    id: "crop-history",
    component: "Crop history",
    checked:
      "Each field's crops for 2015 to 2025 are USDA's satellite-based Cropland Data Layer classes, read from the data files. The app turns the sequence into a sentence, and its tests check that wording.",
    result:
      "No confusion matrix or class-by-class accuracy has been produced. The tests cover the sentence logic only, for example that a corn-heavy sequence is not called “mostly alternating”.",
    doesNotShow:
      "That the crop map is right for these fields. It is USDA's classification, so agreeing with it is not independent proof. Without a separate reference, the best this can become is agreement between two classified products.",
    source: "specs/features/2026-11-14-fe-field-profile; roadmap Phase 14",
    kinds: { ...none, internal: "partly" },
  },
  {
    id: "vegetation",
    component: "Satellite greenness",
    checked: "Not processed yet. The profile shows sample values, labelled as sample.",
    result: "Nothing to report.",
    doesNotShow:
      "Whether greenness adds anything beyond the crop map. Bare-field windows are not computed for any field.",
    source: "roadmap Phase 5 (not started)",
    kinds: none,
  },
  {
    id: "soil",
    component: "Soil",
    checked:
      "The soil calculations (organic matter, water storage, drainage class, texture) are tested against hand-worked cases. The first soil-survey pull for the primary field was recomputed from the raw files and accepted.",
    result:
      "31 tests pass, including a hand-computed 2.48 % organic matter. The primary field's pull has 10 mapped soil units over 43.6 ha, with shares summing to 1.000.",
    doesNotShow:
      "The calculations have not been run on real survey data (the tests use synthetic tables), and the depth and coverage choices are team judgements. The app shows only the soil series and map unit; drainage and organic matter are not loaded.",
    source:
      "specs/features/2026-11-14-ds2-ssurgo-aggregation; docs/sources/ds2-first-pull-review-2026-11-14.md",
    kinds: { ...none, internal: "done" },
  },
  {
    id: "climate",
    component: "Weather indicators",
    checked:
      "Eight indicators from NASA POWER data (heat accumulation, very hot days, frost window, dry spells, rainfall total, mean temperature, reference evapotranspiration) are tested as functions. The first POWER pull for the Iowa research site was compared with that site's station figures in the paper.",
    result:
      "34 tests pass, including a hand-computed heat-accumulation season of 36.0. In the pull, temperature was within 1 °C of the station in 8 of 9 years, but rainfall ran about 11 % lower than the station.",
    doesNotShow:
      "Not run on any demo field's data. Reference evapotranspiration is not independently checked, every threshold is team-proposed, and POWER is a grid about 50 km across, not a field measurement. A comparison with PRISM or CoCoRaHS has not been done.",
    source:
      "specs/features/2026-11-14-ds2-climate-indicators; docs/sources/ds2-first-pull-review-2026-11-14.md",
    kinds: { ...none, internal: "done", otherSource: "partly" },
  },
  {
    id: "marsden",
    component: "Iowa trial figures",
    checked:
      "The nine-year nitrogen and herbicide averages were recomputed from the paper's supplementary records and set beside the figures the paper reports. Twelve targets were compared.",
    result:
      "Applied nitrogen of 74.5, 56.6 and 40.8 kg N/ha/yr and herbicide of 1.925, 0.261 and 0.195 kg/ha/yr reproduce. All 12 targets match. One further check does not (below). 24 tests pass and 1 recorded failure is kept on purpose.",
    doesNotShow:
      "Yields and net returns are attributed to the paper, not recomputed, because the supplement has no plot-level yield tables. One research site over nine seasons does not tell you what will happen on another field.",
    source: "specs/features/2026-11-14-ds2-marsden-reproduction",
    kinds: { ...none, internal: "done", otherSource: "partly" },
  },
  {
    id: "rules",
    component: "Rules for what carries over to your farm",
    checked:
      "16 rules, each tied to one outcome, are tested. No manure limits the nitrogen comparison without touching herbicide. The three outcomes with no evidence can never be claimed. An unstated answer never counts as a yes. Rules version 2026-11-15.1.",
    result:
      "37 tests passed when last recorded on 14 November, and the printed rule document is checked against the code so the two cannot differ. The wording of the cautions was changed on 15 November (version 2026-11-15.1) and a new count has not been recorded here.",
    doesNotShow:
      "No rule has been reviewed by an expert, and no Iowa adviser has been approached. Seven of eight crop claims have no source. Two rules rest on unsourced claims and should be withdrawn if none is found. The heat-distance rule has no published basis. No rule has been run over the 45 fields.",
    source: "specs/features/2026-11-14-ds2-strategy-rules",
    kinds: { ...none, internal: "done" },
  },
  {
    id: "engine",
    component: "The decision engine",
    checked:
      "The engine returns one of three outcomes (worth exploring, comparison with caveats, not enough evidence), with no score and no winner. Tests cover fields in the supported domain, outside it, with missing data, and abstention. The app's copy of the engine is tested to give identical answers in 567 combinations.",
    result:
      "31 engine tests passed and the whole Python suite was recorded as 175 passed, 1 expected failure, on 14 November. The app’s copy of the engine matches the Python engine on all 567 cases against the current rules (version 2026-11-15.1), re-run on 15 November.",
    doesNotShow:
      "Never run on a real field profile, because no indicator values exist yet, so every real result today is “not enough evidence”. It was built without the second data scientist, so its inputs need joint review. Your priorities are recorded but do not change the result.",
    source:
      "specs/features/2026-11-14-ds2-decision-engine; specs/features/2026-11-14-fe-comparison-ui",
    kinds: { ...none, internal: "done" },
  },
  {
    id: "users",
    component: "Farmers and advisers",
    checked:
      "No farmer or adviser has used or reviewed the app yet. The question wording, the plain-language copy and the adviser brief are untested with real people.",
    result:
      "No interviews and no feedback so far. This gap is stated openly rather than filled with invented quotes.",
    doesNotShow:
      "Whether the screens make sense to the people they are for. The app has not had a screen-reader or full keyboard pass. Automated checks cover layout at four screen widths and a clean browser console.",
    source: "roadmap Phase 14; PRD §16 (stakeholder engagement gap acknowledged)",
    kinds: { ...none, internal: "partly" },
  },
];

/** Rows with at least this state for a kind, derived so the summary cannot disagree with the rows. */
export function countByKind(
  rows: readonly ValidationRow[],
): Record<CheckKind, { done: number; partly: number; total: number }> {
  const result = {} as Record<CheckKind, { done: number; partly: number; total: number }>;
  for (const { id } of checkKinds) {
    result[id] = {
      done: rows.filter((row) => row.kinds[id] === "done").length,
      partly: rows.filter((row) => row.kinds[id] === "partly").length,
      total: rows.length,
    };
  }
  return result;
}

/** The one result that does not reconcile, shown on its own so it is never buried. */
export const unreconciled = {
  title: "One result did not match the paper",
  body: "The paper's text gives the two-year system's manufactured nitrogen as 80 kg N/ha/yr. Its own table, weighted the way the paper describes, gives 74.5. The whole gap comes from 2011. Reading 2011 as the maize year alone gives 80.7, which would explain the text, but that is a guess and has not been applied as a correction. Only the authors can say which is right. The check stays marked as failing so it cannot be forgotten.",
  source: "specs/features/2026-11-14-ds2-marsden-reproduction",
} as const;
