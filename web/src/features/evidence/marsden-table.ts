/** The shape of `GET /evidence/marsden`. */
export interface MarsdenRow {
  rotation: string;
  metric: string;
  value: number;
  unit: string;
  evidence_type: string;
  source_id: string;
}

export interface Marsden {
  title: string;
  description: string;
  rows: MarsdenRow[];
  caveats: string[];
  reference: string;
  data_version: string;
}

export const rotations = [
  { id: "2-yr", label: "Two-year", strategy: "A", detail: "maize, soybean" },
  {
    id: "3-yr",
    label: "Three-year",
    strategy: "B",
    detail: "maize, soybean, oat with red clover",
  },
  {
    id: "4-yr",
    label: "Four-year",
    strategy: "C",
    detail: "maize, soybean, oat with alfalfa, alfalfa",
  },
] as const;

/**
 * The names a reader sees. "Applied" nitrogen is manufactured plus manure: never call it "total" nitrogen, which
 * would suggest it counts nitrogen the legumes fixed. The herbicide figure is a mass of active ingredient, not a
 * measure of harm.
 */
const metricLabels: Readonly<Record<string, string>> = {
  manufactured_n: "Manufactured nitrogen fertiliser",
  manure_n: "Manure nitrogen",
  applied_n: "Applied nitrogen (manufactured plus manure)",
  herbicide: "Herbicide active ingredient (mass, not toxicity)",
};
const metricOrder = ["manufactured_n", "manure_n", "applied_n", "herbicide"];

export interface MarsdenLine {
  metric: string;
  label: string;
  unit: string;
  /** Rotation id to value; a rotation with no figure is simply absent. */
  values: Readonly<Record<string, number>>;
  evidenceType: string;
  sourceId: string;
}

/** One line per measure, with a figure per rotation, in a fixed order. Unknown measures follow, labelled as sent. */
export function buildMarsdenLines(rows: readonly MarsdenRow[]): MarsdenLine[] {
  const byMetric = new Map<string, MarsdenLine>();
  for (const row of rows) {
    const line = byMetric.get(row.metric) ?? {
      metric: row.metric,
      label: metricLabels[row.metric] ?? row.metric.replaceAll("_", " "),
      unit: row.unit,
      values: {},
      evidenceType: row.evidence_type,
      sourceId: row.source_id,
    };
    byMetric.set(row.metric, {
      ...line,
      values: { ...line.values, [row.rotation]: row.value },
    });
  }
  const rank = (metric: string) => {
    const index = metricOrder.indexOf(metric);
    return index === -1 ? metricOrder.length : index;
  };
  return [...byMetric.values()].sort((a, b) => rank(a.metric) - rank(b.metric));
}

/** Figures read as they are shown in the paper's tables: three decimals for herbicide, one for nitrogen. */
export const formatFigure = (metric: string, value: number): string =>
  metric === "herbicide" ? value.toFixed(3) : value.toFixed(1);
