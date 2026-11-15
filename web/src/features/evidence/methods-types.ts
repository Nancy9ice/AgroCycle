/** The shapes of `GET /sources`, `GET /indicators`, `GET /lineage/{id}` and `GET /health`. */
export interface Source {
  source_id: string;
  provider: string;
  product: string;
  product_version: string;
  url: string;
  spatial_resolution: string;
  temporal_resolution: string;
  geographic_coverage: string;
  historical_coverage: string;
  retrieval_date: string;
  licence: string;
  known_limitations: string;
  evidence_type: string;
  file_count: number;
  total_bytes: number;
}

export interface IndicatorSummary {
  indicator_id: string;
  label: string;
  formula: string;
  aggregation_window: string;
  scale: string;
  resolution: string;
  evidence_type: string;
  limitation: string;
}

export interface Lineage {
  indicator_id: string;
  label: string;
  source_ids: string[];
  variables: string[];
  formula: string;
  aggregation_window: string;
  spatial_support: string;
  scale: string;
  resolution: string;
  evidence_type: string;
  missing_data_rule: string;
  interpretation: string;
  limitation: string;
  code_version: string;
}

export interface Health {
  rules_version: string;
  data_version: string;
}
