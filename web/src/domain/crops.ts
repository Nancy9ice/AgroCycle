/**
 * Crops as they appear in the USDA Cropland Data Layer history. One letter per year, the
 * codes DE uses in `field_selection_notes.csv`. Kept separate from the rotation phases in
 * `strategies.ts`, which describe scenarios rather than recorded history.
 */

export type CropCode = "C" | "S" | "G" | "A" | "H" | "O" | "L" | "X";

export interface Crop {
  code: CropCode;
  label: string;
  /** Tailwind background class for the swatch. */
  swatch: string;
}

export const crops: Record<CropCode, Crop> = {
  C: { code: "C", label: "Corn", swatch: "bg-crop-maize" },
  S: { code: "S", label: "Soybean", swatch: "bg-crop-soybean" },
  G: { code: "G", label: "Grass or pasture", swatch: "bg-crop-grass" },
  A: { code: "A", label: "Alfalfa", swatch: "bg-crop-alfalfa" },
  H: { code: "H", label: "Other hay", swatch: "bg-crop-hay" },
  O: { code: "O", label: "Oats", swatch: "bg-crop-oat" },
  L: { code: "L", label: "Clover", swatch: "bg-crop-clover" },
  X: { code: "X", label: "Other crop", swatch: "bg-crop-other" },
};

export const isCropCode = (value: string): value is CropCode => value in crops;
