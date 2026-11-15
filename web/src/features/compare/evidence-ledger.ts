/**
 * The evidence ledger: for one comparison, which statements rest on which kind of evidence, and whose
 * land that evidence is about (`domain/evidence.ts`, `evidenceLayers`).
 *
 * It is the one place that decides a statement's layer. The compare screen and the adviser brief both
 * render this, so a figure from one research farm can never look like a measurement of the farmer's
 * own field on one screen and not the other.
 *
 * It holds no numbers and no policy. It reads what the engine returned (`Decision`) and, when there
 * is one, the field profile, and it files each thing under a layer. Unknown stays unknown: a missing
 * input is listed as missing in its layer, never dropped and never shown as fine.
 */
import {
  evidenceLayerById,
  evidenceLayers,
  type EvidenceLayer,
  type EvidenceLayerId,
  type EvidenceTypeId,
} from "@/domain/evidence";
import type { FieldProfile } from "@/features/profile/types";
import { questions } from "@/features/priorities/questions";
import { priorityLabels } from "./priority-links";
import { ruleTable } from "./rules";
import type { Decision, OutcomeAssessment } from "./types";

export type LedgerItemState =
  /** In the comparison and available. */
  | "in_comparison"
  /** Something the rules read that nobody has established. */
  | "missing"
  /** A research finding the engine will not state for this field. */
  | "withheld"
  /** No data measures this on a field, so we say nothing. */
  | "not_assessed"
  /** Something the farmer told us or a choice we made. */
  | "recorded"
  /** A stand-in value from the sample preview. Not this field's data. */
  | "sample";

export interface LedgerItem {
  id: string;
  label: string;
  detail?: string;
  state: LedgerItemState;
  evidenceType?: EvidenceTypeId;
  source?: string | null;
}

export interface LedgerLayer {
  /** 1 to 6, in the order the layers are shown. */
  number: number;
  layer: EvidenceLayer;
  items: readonly LedgerItem[];
  /** Shown when the layer has nothing in it, so an empty layer is stated, not hidden. */
  emptyNote: string;
}

export interface EvidenceLedger {
  headline: string;
  layers: readonly LedgerLayer[];
}

export const ledgerStateCopy: Record<
  LedgerItemState,
  { label: string; glyph: string; tone: "good" | "caution" | "stop" | "neutral" }
> = {
  in_comparison: { label: "Used", glyph: "✓", tone: "good" },
  missing: { label: "Not available", glyph: "?", tone: "stop" },
  withheld: { label: "Held back", glyph: "?", tone: "stop" },
  not_assessed: { label: "Not assessed", glyph: "–", tone: "neutral" },
  recorded: { label: "Recorded", glyph: "●", tone: "neutral" },
  sample: { label: "Sample value, not your field", glyph: "~", tone: "caution" },
};

/**
 * What the engine's rules read from the field, and which layer each belongs to. The engine reports
 * only what is unknown (`Decision.unknowns`), so anything not listed there was known.
 */
const RULE_INPUTS: ReadonlyArray<{
  key: string;
  layer: EvidenceLayerId;
  label: string;
  /** True for the inputs the sample preview replaces (the API and the offline copy substitute the same ones). */
  sampledInPreview: boolean;
}> = [
  {
    key: "county",
    layer: "field_retrieved",
    label: "County the field is in",
    sampledInPreview: false,
  },
  {
    key: "crop_history_is_maize_soybean",
    layer: "field_derived",
    label: "Whether recent crops follow a corn–soybean rotation",
    sampledInPreview: false,
  },
  {
    key: "gdd_season_difference_vs_marsden",
    layer: "field_derived",
    label: "Growing-season warmth compared with the Iowa trial site",
    sampledInPreview: true,
  },
  {
    key: "frost_free_days",
    layer: "field_derived",
    label: "Frost-free days",
    sampledInPreview: true,
  },
  {
    key: "indicator gdd",
    layer: "field_derived",
    label: "Growing degree days (heat accumulation)",
    sampledInPreview: true,
  },
  {
    key: "indicator precipitation_total",
    layer: "field_derived",
    label: "Growing-season rainfall total",
    sampledInPreview: true,
  },
  {
    key: "indicator frost_window",
    layer: "field_derived",
    label: "The frost-free window",
    sampledInPreview: true,
  },
  {
    key: "dominant_drainage_class",
    layer: "soil_survey",
    label: "How well the soil drains",
    sampledInPreview: false,
  },
  {
    key: "indicator om_r_0_30cm",
    layer: "soil_survey",
    label: "Soil organic matter, top 30 cm",
    sampledInPreview: true,
  },
];

/** The layer a research outcome belongs to. Anything the engine will not back with evidence is "unknown". */
export function layerForOutcome(outcome: OutcomeAssessment): EvidenceLayerId {
  if (!outcome.claimable) return "assumed_or_unknown";
  if (outcome.evidence_type === "experimental") return "marsden_experiment";
  if (outcome.evidence_type === "published") return "published_finding";
  return "assumed_or_unknown";
}

const EMPTY_NOTES: Record<EvidenceLayerId, string> = {
  field_retrieved: "Nothing was looked up for this field.",
  field_derived: "Nothing was worked out for this field.",
  soil_survey: "No soil survey values were used.",
  marsden_experiment:
    "No finding from the Marsden experiment is shown for this field, so nothing here is stated about benefits.",
  published_finding: "No published finding is shown for this field.",
  assumed_or_unknown: "Nothing assumed and nothing unknown.",
};

function cropHistoryItem(profile: FieldProfile | undefined): LedgerItem | undefined {
  const section = profile?.cropHistory;
  const years = section?.data?.years;
  if (!section || !years || years.length === 0) return undefined;
  const first = years[0].year;
  const last = years[years.length - 1].year;
  return {
    id: "crop-history",
    label: `What was grown, ${first} to ${last}`,
    detail: `${section.provenance?.source ?? "Crop map"}. A satellite classification, not a farm record.`,
    state: "in_comparison",
    evidenceType: section.provenance?.technical.evidenceType ?? "classified",
    source: section.provenance?.source,
  };
}

function outcomeItem(outcome: OutcomeAssessment): LedgerItem {
  const shown = outcome.statement !== null;
  return {
    id: `outcome-${outcome.outcome_id}`,
    label: outcome.label,
    detail: shown
      ? "Shown, with its caution."
      : "Not shown for this field. Missing information is not treated as good or bad news.",
    state: shown ? "in_comparison" : "withheld",
    evidenceType: outcome.evidence_type ?? undefined,
    source: outcome.source,
  };
}

function answerItems(decision: Decision): LedgerItem[] {
  const items: LedgerItem[] = [];
  for (const question of questions) {
    if (!("engineKey" in question) || !question.engineKey) continue;
    const value = decision.constraints_recorded[question.engineKey];
    items.push({
      id: `answer-${question.id}`,
      label: question.label,
      detail:
        value === null ? "You have not said." : value ? "You said yes." : "You said no.",
      state: value === null ? "missing" : "recorded",
      evidenceType: "assumption",
    });
  }
  return items;
}

function reviewItem(decision: Decision): LedgerItem {
  const sameVersion = decision.rules_version === ruleTable.rulesVersion;
  const unreviewed = ruleTable.rules.filter(
    (r) => r.review === "not_expert_reviewed",
  ).length;
  const detail = !sameVersion
    ? "The review status of this version of the rules is not known to this page."
    : unreviewed === ruleTable.rules.length
      ? "None of the rules has been reviewed by an agronomist."
      : `${unreviewed} of ${ruleTable.rules.length} rules have not been reviewed by an agronomist.`;
  return {
    id: "rules-review",
    label: "The rules that decide whether the research applies to you",
    detail: `Proposed by the AgroCycle team. ${detail}`,
    state: "recorded",
    evidenceType: "assumption",
  };
}

/** Files everything in a comparison under the layer it rests on. */
export function buildEvidenceLedger(
  decision: Decision,
  profile?: FieldProfile,
  options: { preview?: boolean } = {},
): EvidenceLedger {
  const unknown = new Set(decision.unknowns);
  const byLayer = new Map<EvidenceLayerId, LedgerItem[]>(
    evidenceLayers.map((layer) => [layer.id, []]),
  );
  const add = (layer: EvidenceLayerId, item: LedgerItem) =>
    byLayer.get(layer)!.push(item);

  const history = cropHistoryItem(profile);
  if (history) add("field_retrieved", history);

  for (const input of RULE_INPUTS) {
    const missing = unknown.has(input.key);
    const sample = options.preview === true && input.sampledInPreview;
    add(input.layer, {
      id: `input-${input.key}`,
      label: input.label,
      state: sample ? "sample" : missing ? "missing" : "in_comparison",
      detail: sample
        ? "Preview only: a made-up value that is known and fine, standing in for the real measurement."
        : missing
          ? "Not available for this field, so it is not treated as fine."
          : undefined,
    });
  }

  for (const outcome of decision.outcomes) {
    const layer = layerForOutcome(outcome);
    if (layer === "assumed_or_unknown") {
      add(layer, {
        id: `outcome-${outcome.outcome_id}`,
        label: outcome.label,
        detail:
          "We have no data that measures this on a field, so we say nothing about it.",
        state: "not_assessed",
      });
    } else {
      add(layer, outcomeItem(outcome));
    }
  }

  for (const item of answerItems(decision)) add("assumed_or_unknown", item);
  if (decision.priorities_recorded.length > 0) {
    add("assumed_or_unknown", {
      id: "priorities",
      label: "Priorities you marked high",
      detail: `${decision.priorities_recorded
        .map((id) => priorityLabels[id] ?? id)
        .join("; ")}. These change what the page points out, not the result.`,
      state: "recorded",
      evidenceType: "assumption",
    });
  }
  add("assumed_or_unknown", reviewItem(decision));

  const shown = decision.outcomes.filter(
    (o) => layerForOutcome(o) !== "assumed_or_unknown" && o.statement !== null,
  );
  const headline =
    shown.length > 0
      ? "Every statement about benefits on this page comes from research (layers 4 and 5), not from measurements of your field. What was looked up for your field (layers 1 to 3) only decides whether that research can be applied to it."
      : "No statement about benefits is shown for this field. What was looked up for it (layers 1 to 3) is used only to decide whether the research can be applied, and here it could not.";

  return {
    headline: options.preview
      ? `Sample preview: the values marked "sample" below are not this field's data. ${headline}`
      : headline,
    layers: evidenceLayers.map((layer, index) => ({
      number: index + 1,
      layer: evidenceLayerById[layer.id],
      items: byLayer.get(layer.id)!,
      emptyNote: EMPTY_NOTES[layer.id],
    })),
  };
}
