/**
 * The field-profile contract: what the profile screen needs from `GET /fields/{id}/profile`.
 * This is a proposal for BE to compare with the OpenAPI draft. Names follow
 * `specs/tech-stack.md` (evidence_type, scale, indicator id). The UI renders these values and
 * never classifies anything itself: states like "bare" or "unknown" arrive already decided.
 */
import type { CropCode } from "@/domain/crops";
import type { EvidenceTypeId } from "@/domain/evidence";

/**
 * - `available`: real data from the pipeline or the committed data files.
 * - `sample`: placeholder values shown until the pipeline exists. Must be labelled in the UI.
 * - `not_loaded`: nothing to show yet.
 */
export type SectionStatus = "available" | "sample" | "not_loaded";

/** The record behind every material output (PRD §6.1, FR-12). */
export interface Provenance {
  title: string;
  whatItIs: string;
  source: string;
  sourceUrl?: string;
  /** How coarse or uncertain it is, in plain language. */
  precision: string;
  /** What is missing or skipped. */
  gaps: string;
  technical: {
    evidenceType: EvidenceTypeId;
    scale: string;
    indicatorId: string;
    variable?: string;
    product?: string;
    version?: string;
    retrieved?: string;
  };
}

export interface ProfileSection<T> {
  status: SectionStatus;
  data: T | null;
  provenance: Provenance | null;
}

export interface CropYear {
  year: number;
  code: CropCode;
}

export interface CropHistory {
  years: readonly CropYear[];
  /** One plain sentence describing the sequence. */
  summary: string;
  /** Years whose crop repeats the previous year's, if any. */
  repeatedYears: readonly number[];
}

export interface Indicator {
  id: string;
  label: string;
  value: string;
  /** What the value means, in plain language. */
  context: string;
  provenance: Provenance;
}

export interface ClimateProfile {
  /** e.g. "Averages over 2015 to 2024". */
  periodLabel: string;
  indicators: readonly Indicator[];
}

export type VegetationState = "growing" | "bare" | "unknown";

export interface VegetationMonth {
  /** 1 to 12. */
  month: number;
  /** Mean greenness index, or null when there are too few clear images to say. */
  ndvi: number | null;
  /** Number of clear (cloud-screened) images behind the value. */
  clearImages: number;
  state: VegetationState;
}

export interface VegetationProfile {
  months: readonly VegetationMonth[];
  /** What the months say, written by the data layer. */
  interpretation: string;
  /** Why some months are "unknown". */
  unknownReason: string;
  /** How "bare" was decided, e.g. the index threshold. */
  barePrinciple: string;
}

export interface SoilProfile {
  series: string;
  mapUnit: string;
  /** Where in the field the soil was read. */
  samplingNote: string;
  /** Properties we do not have yet; shown as "not loaded", never as a value. */
  notLoaded: readonly string[];
}

export interface FieldProfile {
  fieldId: string;
  cropHistory: ProfileSection<CropHistory>;
  climate: ProfileSection<ClimateProfile>;
  vegetation: ProfileSection<VegetationProfile>;
  soil: ProfileSection<SoilProfile>;
}
