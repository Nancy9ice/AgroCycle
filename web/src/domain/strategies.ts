/**
 * The three rotation strategies compared by AgroCycle (PRD §2.2).
 * They mirror the systems in the Marsden Farm experiment (Davis et al., 2012) and are
 * comparison scenarios, not prescriptions. Keep in sync with the engine's strategy profiles.
 */

export type CropPhaseId =
  "maize" | "soybean" | "oat-red-clover" | "oat-alfalfa" | "alfalfa";

export interface CropPhase {
  id: CropPhaseId;
  label: string;
  /** Tailwind background class for the phase swatch. */
  swatch: string;
}

export const cropPhases: Record<CropPhaseId, CropPhase> = {
  maize: { id: "maize", label: "Corn", swatch: "bg-crop-maize" },
  soybean: { id: "soybean", label: "Soybean", swatch: "bg-crop-soybean" },
  "oat-red-clover": {
    id: "oat-red-clover",
    label: "Oat + red clover",
    swatch: "bg-crop-oat",
  },
  "oat-alfalfa": { id: "oat-alfalfa", label: "Oat + alfalfa", swatch: "bg-crop-oat" },
  alfalfa: { id: "alfalfa", label: "Alfalfa", swatch: "bg-crop-alfalfa" },
};

export type StrategyId = "A" | "B" | "C";

export interface Strategy {
  id: StrategyId;
  name: string;
  kind: "Existing system" | "Diversified option";
  summary: string;
  /** Crop phase for each year of the rotation, in order. */
  phases: readonly CropPhaseId[];
}

export const strategies: readonly Strategy[] = [
  {
    id: "A",
    name: "Keep it as it is",
    kind: "Existing system",
    summary: "The two-year corn–soybean rotation you already grow.",
    phases: ["maize", "soybean"],
  },
  {
    id: "B",
    name: "Three-year rotation",
    kind: "Diversified option",
    summary: "Adds a year of oat with red clover sown underneath.",
    phases: ["maize", "soybean", "oat-red-clover"],
  },
  {
    id: "C",
    name: "Four-year rotation",
    kind: "Diversified option",
    summary: "Adds oat with alfalfa, then a full year of alfalfa.",
    phases: ["maize", "soybean", "oat-alfalfa", "alfalfa"],
  },
] as const;
