/** The shape of `GET /fields/{id}/season-summary`. */
export interface SeasonValue {
  year: number;
  value: number | null;
  status: string;
  window_start: string;
  window_end: string;
  unknown_reason: string;
}

export interface SeasonExtreme {
  year: number;
  value: number;
}

/** DS2's record of what an indicator counts and the threshold behind it. */
export interface SeasonThreshold {
  what_it_counts: string;
  threshold: string;
  unit: string;
  evidence_basis: "experimental" | "team_proposed" | "assumption";
  review: "not_expert_reviewed" | "expert_reviewed";
  limitation: string;
  code_version: string;
}

export interface SeasonIndicator {
  indicator_id: string;
  label: string;
  unit: string;
  evidence_type: string;
  scale: string;
  source: string;
  formula: string;
  limitation: string;
  threshold: SeasonThreshold | null;
  seasons: SeasonValue[];
  seasons_used: number;
  seasons_total: number;
  highest: SeasonExtreme | null;
  lowest: SeasonExtreme | null;
}

export interface SeasonSummary {
  field_id: string;
  period: string;
  indicators: SeasonIndicator[];
  caveats: string[];
  data_version: string;
}
