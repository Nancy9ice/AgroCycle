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
}

export const evidenceTypes: Record<EvidenceTypeId, EvidenceType> = {
  observed: {
    id: "observed",
    label: "Observed product",
    meaning: "A value supplied directly by an instrument, agency or data provider.",
  },
  derived: {
    id: "derived",
    label: "Derived indicator",
    meaning: "A calculation made from one or more observed variables.",
  },
  classified: {
    id: "classified",
    label: "Classified output",
    meaning: "A class assigned by an algorithm or agency, such as a crop type.",
  },
  survey: {
    id: "survey",
    label: "Survey information",
    meaning: "Mapped or sampled soil information, not a test from this exact field.",
  },
  model_reanalysis: {
    id: "model_reanalysis",
    label: "Model estimate",
    meaning: "A model-based estimate for an area, not a local measurement.",
  },
  experimental: {
    id: "experimental",
    label: "Experimental record",
    meaning: "Data collected inside a research experiment.",
  },
  published: {
    id: "published",
    label: "Published finding",
    meaning: "A conclusion reported in a scientific paper.",
  },
  assumption: {
    id: "assumption",
    label: "Your input or assumption",
    meaning: "Something you told us, or a design assumption we made.",
  },
};
