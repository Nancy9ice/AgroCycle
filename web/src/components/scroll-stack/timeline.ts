/** The scroll timeline, as fractions of the pinned section's progress (0 → 1). */
export const TIMELINE: Record<"introFadeOut" | "illustrationFadeIn" | "cards", number[]> =
  {
    introFadeOut: [0, 0.18],
    illustrationFadeIn: [0.25, 0.38],
    cards: [0.38, 0.88],
    // 0.88 → 1 is a hold: the last card stays in place, then the section unpins.
  };

/** How far above its resting place a waiting card peeks, as a fraction of the card index distance. */
export const PEEK = 0.6;

export const clamp = (value: number, min: number, max: number) =>
  Math.min(max, Math.max(min, value));
