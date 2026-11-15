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
