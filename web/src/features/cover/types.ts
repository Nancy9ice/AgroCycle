/** The shape of `GET /fields/{id}/cover-calendar`. */
export type CoverState = "bare" | "likely_bare" | "green" | "unknown";

export interface CoverMonth {
  month: number;
  state: CoverState;
  usable_images: number;
  bare_days: number;
  days: number;
}

export interface CoverYear {
  year: number;
  months: CoverMonth[];
  bare_months: number;
  months_with_images: number;
}

export interface BareWindow {
  start: string;
  end: string;
  bare_days: number;
  confidence: string;
  seen_in_images: boolean;
}

export interface CoverCalendar {
  field_id: string;
  source: string;
  evidence_type: string;
  scale: string;
  ndvi_threshold: number;
  min_bare_days: number;
  years: CoverYear[];
  bare_windows: BareWindow[];
  legend: Record<CoverState, string>;
  caveats: string[];
  data_version: string;
}
