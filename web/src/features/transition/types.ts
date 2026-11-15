/** The shape of `GET /strategies/{id}/transition`. */
export interface TransitionStep {
  year: number;
  crop: string;
  action: string;
  needs: string[];
  timing_note: string;
  timing_established: boolean;
  evidence_basis: "experimental" | "team_proposed" | "assumption";
  source: string;
  shows_past_weather: boolean;
}

export interface Readiness {
  constraint: string;
  label: string;
  answer: boolean | null;
  status: "yes" | "no" | "not_answered";
  step_year: number;
}

export interface Transition {
  strategy_id: string;
  label: string;
  rotation: string;
  rules_version: string;
  steps: TransitionStep[];
  readiness: Readiness[] | null;
  caveats: string[];
  data_version: string;
}
