import type { ReactNode } from "react";
import type { CropPhaseId } from "@/domain/strategies";

/** Shared pieces for the decorative illustrations in the scroll-stack sections. */

export const cropFill: Record<CropPhaseId, string> = {
  maize: "var(--color-crop-maize)",
  soybean: "var(--color-crop-soybean)",
  "oat-red-clover": "var(--color-crop-oat)",
  "oat-alfalfa": "var(--color-crop-oat)",
  alfalfa: "var(--color-crop-alfalfa)",
};

export const ACCENT = "#e5eab0";
export const INK = "#0c1d14";
export const LABEL = {
  fontFamily: "var(--font-mono)",
  fontSize: 13,
  letterSpacing: "0.08em",
  textTransform: "uppercase",
} as const;

export function Frame({ children }: { children: ReactNode }) {
  return (
    <svg viewBox="0 0 520 520" aria-hidden focusable="false" role="presentation">
      {children}
    </svg>
  );
}
