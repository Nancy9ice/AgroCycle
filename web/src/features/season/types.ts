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

export interface SeasonIndicator {
  indicator_id: string;
  label: string;
  unit: string;
  evidence_type: string;
  scale: string;
  source: string;
  formula: string;
  limitation: string;
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
