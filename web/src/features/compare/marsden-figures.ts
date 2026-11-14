import type { StrategyKey } from "./types";

/**
 * The reproduced Marsden Farm figures (Davis et al. 2012 supplementary records, reproduced by
 * DS2 in `transform/marsden`): rotation-area-weighted nine-year averages from one site.
 *
 * DS2's outcome statements contain these numbers as prose. They are typed once here so the screen
 * can show them per strategy, and `marsden-figures.test.ts` fails if they stop appearing in
 * DS2's statements, so the two cannot drift apart.
 */
export interface FigureRow {
  label: string;
  values: Readonly<Record<StrategyKey, number>>;
}

export interface OutcomeFigures {
  unit: string;
  rows: readonly FigureRow[];
}

export const marsdenFigures: Readonly<Record<string, OutcomeFigures>> = {
  applied_n_reduction: {
    unit: "kg N per hectare per year",
    rows: [
      {
        label: "Applied nitrogen (manufactured plus manure)",
        values: { A: 74.5, B: 56.6, C: 40.8 },
      },
      {
        label: "Of which manufactured fertiliser",
        values: { A: 74.5, B: 16.7, C: 10.9 },
      },
    ],
  },
  herbicide_reduction: {
    unit: "kg active ingredient per hectare per year",
    rows: [{ label: "Herbicide applied", values: { A: 1.925, B: 0.261, C: 0.195 } }],
  },
};
