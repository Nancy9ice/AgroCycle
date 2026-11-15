/**
 * Evidence-type labels (PRD §6.2). Every material output in the product carries one.
 * The ids match the `evidence_type` Enum used in ClickHouse and the API.
 */

export type EvidenceTypeId =
  | "observed"
  | "derived"
  | "classified"
  | "survey"
  | "model_reanalysis"
  | "experimental"
  | "published"
  | "assumption";

export interface EvidenceType {
  id: EvidenceTypeId;
  /** Short label for badges. */
  label: string;
  /** Plain-language meaning, for tooltips and legends. */
  meaning: string;
  /**
   * One short sentence a farmer can read under a number: what kind of evidence it is and how far to trust
   * it for their own field. The technical scale (grid size, pixel size) stays in the details drawer.
   */
  plain: string;
}

export const evidenceTypes: Record<EvidenceTypeId, EvidenceType> = {
  observed: {
    id: "observed",
    label: "Observed product",
    meaning: "A value supplied directly by an instrument, agency or data provider.",
    plain: "Measured and reported by an instrument or an agency.",
  },
  derived: {
    id: "derived",
    label: "Derived indicator",
    meaning: "A calculation made from one or more observed variables.",
    plain: "Worked out from satellite or weather measurements.",
  },
  classified: {
    id: "classified",
    label: "Classified output",
    meaning: "A class assigned by an algorithm or agency, such as a crop type.",
    plain: "A crop type picked out from satellite images, so it can be wrong.",
  },
  survey: {
    id: "survey",
    label: "Survey information",
    meaning: "Mapped or sampled soil information, not a test from this exact field.",
    plain: "From soil maps, not a test on your field.",
  },
  model_reanalysis: {
    id: "model_reanalysis",
    label: "Model estimate",
    meaning: "A model-based estimate for an area, not a local measurement.",
    plain: "Weather for your area, not measured on your field.",
  },
  experimental: {
    id: "experimental",
    label: "Experimental record",
    meaning: "Data collected inside a research experiment.",
    plain: "From a research farm, not from yours.",
  },
  published: {
    id: "published",
    label: "Published finding",
    meaning: "A conclusion reported in a scientific paper.",
    plain: "Reported in a research paper.",
  },
  assumption: {
    id: "assumption",
    label: "Your input or assumption",
    meaning: "Something you told us, or a design assumption we made.",
    plain: "What you told us, or a choice we made.",
  },
};

/**
 * The evidence hierarchy shown to a farmer on the comparison and in the adviser brief. Where the
 * evidence types above say *what kind* of evidence a value is, the layers say *whose land it is
 * about*, which is what decides how far a farmer can lean on it. The order runs from the most
 * about-your-field to the least.
 *
 * Which layer a value belongs to is decided by `features/compare/evidence-ledger.ts`, never by a
 * component, so the same statement can never sit in two layers on two screens.
 */
export type EvidenceLayerId =
  | "field_retrieved"
  | "field_derived"
  | "soil_survey"
  | "marsden_experiment"
  | "published_finding"
  | "assumed_or_unknown";

/** Whose land the evidence is about. */
export type EvidenceAbout =
  "your_field" | "your_area" | "research_farm" | "paper" | "you";

export interface EvidenceLayer {
  id: EvidenceLayerId;
  title: string;
  about: EvidenceAbout;
  /** The scope in one short phrase, shown as a tag next to the title. */
  scope: string;
  /** One or two sentences: what this layer can and cannot tell the farmer. */
  meaning: string;
}

export const evidenceLayers: readonly EvidenceLayer[] = [
  {
    id: "field_retrieved",
    title: "Looked up for your field",
    about: "your_field",
    scope: "Your field’s location",
    meaning:
      "Public records and satellite products fetched for where your field is. The crop map is a satellite classification and can be wrong, and weather is a model estimate for an area about 50 km across, not a gauge on your field.",
  },
  {
    id: "field_derived",
    title: "Worked out from those",
    about: "your_field",
    scope: "Calculated by us",
    meaning:
      "Numbers we calculated from the records above, such as growing-season warmth. They are only as good as what went in.",
  },
  {
    id: "soil_survey",
    title: "From the soil survey",
    about: "your_area",
    scope: "Mapped soil, not a soil test",
    meaning:
      "What the national soil survey maps for the soil units under your field. It is not a sample taken from your field.",
  },
  {
    id: "marsden_experiment",
    title: "From the Marsden experiment",
    about: "research_farm",
    scope: "One research farm, not your field",
    meaning:
      "Records from a long-running trial at one research farm in Iowa (nine seasons), reproduced by AgroCycle. They show what happened there, not what will happen on your land.",
  },
  {
    id: "published_finding",
    title: "Published, not reproduced by us",
    about: "paper",
    scope: "A research paper, not rechecked",
    meaning:
      "Conclusions reported in the Marsden paper (Davis et al., 2012). AgroCycle has not independently reproduced them, and they come from the same single research farm.",
  },
  {
    id: "assumed_or_unknown",
    title: "Assumed or unknown",
    about: "you",
    scope: "Your answers, our rules, and gaps",
    meaning:
      "What you told us, the rules we proposed (no agronomist has reviewed them) and everything nobody has established. Unknown is never treated as good or bad news.",
  },
];

export const evidenceLayerById: Readonly<Record<EvidenceLayerId, EvidenceLayer>> =
  Object.fromEntries(evidenceLayers.map((layer) => [layer.id, layer])) as Record<
    EvidenceLayerId,
    EvidenceLayer
  >;
