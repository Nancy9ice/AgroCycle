-- The 17 tables found in the agrocycle database on 2026-11-14, created 2026-11-13 21:42 outside this repo.
-- Dropped on 2026-11-14 by decision (Phase 2 DE) in favour of schema/001_core.sql. All were empty.
-- Archived with SHOW CREATE TABLE so they can be recreated if needed. Not applied by common.migrate.

CREATE TABLE agrocycle.analyses
(
    `analysis_id` String,
    `field_id` String,
    `created_at` DateTime64(3, 'UTC') DEFAULT now64(3),
    `engine_version` String,
    `data_version` String,
    `outcome_type` Enum8('worth_exploring' = 1, 'qualified_comparison' = 2, 'abstention' = 3),
    `request_json` String,
    `response_json` String
)
ENGINE = MergeTree
ORDER BY analysis_id
SETTINGS index_granularity = 8192;

CREATE TABLE agrocycle.ask_log
(
    `ask_id` UUID DEFAULT generateUUIDv4(),
    `analysis_id` Nullable(String),
    `field_id` String,
    `asked_at` DateTime64(3, 'UTC') DEFAULT now64(3),
    `audience` Enum8('farmer' = 1, 'adviser' = 2),
    `question` String,
    `answer` String,
    `citations` Array(String),
    `refused` Bool,
    `model` LowCardinality(String)
)
ENGINE = MergeTree
ORDER BY (field_id, asked_at, ask_id)
SETTINGS index_granularity = 8192;

CREATE TABLE agrocycle.bare_windows
(
    `field_id` String,
    `year` UInt16,
    `month` UInt8,
    `state` Enum8('covered' = 1, 'bare' = 2, 'unknown' = 3),
    `valid_obs` UInt16,
    `indicator_id` String,
    `run_id` String,
    `loaded_at` DateTime64(3, 'UTC') DEFAULT now64(3)
)
ENGINE = ReplacingMergeTree(loaded_at)
ORDER BY (field_id, year, month)
SETTINGS index_granularity = 8192;

CREATE TABLE agrocycle.climate_daily
(
    `field_id` String,
    `variable` LowCardinality(String),
    `date` Date,
    `value` Nullable(Float64),
    `unit` LowCardinality(String),
    `source_id` LowCardinality(String),
    `run_id` String,
    `loaded_at` DateTime64(3, 'UTC') DEFAULT now64(3)
)
ENGINE = ReplacingMergeTree(loaded_at)
PARTITION BY toYear(date)
ORDER BY (field_id, variable, date)
SETTINGS index_granularity = 8192;

CREATE TABLE agrocycle.crop_history
(
    `field_id` String,
    `year` UInt16,
    `cdl_class_code` UInt16,
    `cdl_class_name` LowCardinality(String),
    `share_pct` Float32,
    `resolution_m` UInt16,
    `product_version` String,
    `indicator_id` String,
    `run_id` String,
    `loaded_at` DateTime64(3, 'UTC') DEFAULT now64(3)
)
ENGINE = ReplacingMergeTree(loaded_at)
ORDER BY (field_id, year, cdl_class_code)
SETTINGS index_granularity = 8192;

CREATE TABLE agrocycle.data_sources
(
    `source_id` LowCardinality(String),
    `provider` String,
    `product` String,
    `product_version` String,
    `url` String,
    `variables` Array(String),
    `spatial_resolution` String,
    `temporal_resolution` String,
    `coverage` String,
    `retrieval_date` Date,
    `licence` String,
    `known_limitations` String,
    `raw_s3_uri` String,
    `sha256` String,
    `loaded_at` DateTime64(3, 'UTC') DEFAULT now64(3)
)
ENGINE = ReplacingMergeTree(loaded_at)
ORDER BY source_id
SETTINGS index_granularity = 8192;

CREATE TABLE agrocycle.engine_rules
(
    `rules_version` String,
    `rule_set` LowCardinality(String),
    `rule_id` String,
    `rule_json` String,
    `source_ref` String,
    `reviewed_by` String,
    `loaded_at` DateTime64(3, 'UTC') DEFAULT now64(3)
)
ENGINE = ReplacingMergeTree(loaded_at)
ORDER BY (rules_version, rule_set, rule_id)
SETTINGS index_granularity = 8192;

CREATE TABLE agrocycle.feedback
(
    `feedback_id` UUID DEFAULT generateUUIDv4(),
    `submitted_at` DateTime64(3, 'UTC') DEFAULT now64(3),
    `role` Enum8('farmer' = 1, 'adviser' = 2, 'researcher' = 3, 'other' = 4),
    `usefulness` UInt8,
    `clarity` UInt8,
    `what_was_missing` String,
    `would_use` Nullable(Enum8('yes' = 1, 'maybe' = 2, 'no' = 3)),
    `contact` Nullable(String),
    `contact_consent` Bool DEFAULT false,
    `field_id` Nullable(String),
    `analysis_id` Nullable(String)
)
ENGINE = MergeTree
ORDER BY (submitted_at, feedback_id)
SETTINGS index_granularity = 8192;

CREATE TABLE agrocycle.field_indicators
(
    `field_id` String,
    `indicator_id` String,
    `category` Enum8('climate' = 1, 'soil' = 2, 'vegetation' = 3, 'water' = 4, 'regional' = 5, 'context' = 6),
    `value` Nullable(Float64),
    `unit` LowCardinality(String),
    `status` Enum8('available' = 1, 'partial' = 2, 'unknown' = 3, 'not_assessed' = 4),
    `window_start` Nullable(Date),
    `window_end` Nullable(Date),
    `valid_obs` Nullable(UInt32),
    `unknown_reason` Nullable(String),
    `run_id` String,
    `loaded_at` DateTime64(3, 'UTC') DEFAULT now64(3)
)
ENGINE = ReplacingMergeTree(loaded_at)
ORDER BY (field_id, indicator_id)
SETTINGS index_granularity = 8192;

CREATE TABLE agrocycle.field_source_coverage
(
    `field_id` String,
    `source_id` LowCardinality(String),
    `status` Enum8('available' = 1, 'partial' = 2, 'unknown' = 3, 'not_assessed' = 4),
    `note` String,
    `run_id` String,
    `loaded_at` DateTime64(3, 'UTC') DEFAULT now64(3)
)
ENGINE = ReplacingMergeTree(loaded_at)
ORDER BY (field_id, source_id)
SETTINGS index_granularity = 8192;

CREATE TABLE agrocycle.fields
(
    `field_id` String,
    `name` String,
    `county` LowCardinality(String),
    `area_ha` Float64,
    `boundary_source` Enum8('demo' = 1, 'farmer_provided' = 2, 'drawn' = 3),
    `is_demo` Bool,
    `in_pilot_area` Bool,
    `is_preprocessed` Bool DEFAULT false,
    `geometry_geojson` String,
    `centroid_lon` Float64,
    `centroid_lat` Float64,
    `created_at` DateTime64(3, 'UTC') DEFAULT now64(3)
)
ENGINE = ReplacingMergeTree(created_at)
ORDER BY field_id
SETTINGS index_granularity = 8192;

CREATE TABLE agrocycle.ground_truth
(
    `field_id` String,
    `year` UInt16,
    `crop` LowCardinality(String),
    `notes` String,
    `entered_by` Enum8('farmer' = 1, 'adviser' = 2, 'other' = 3),
    `entered_at` DateTime64(3, 'UTC') DEFAULT now64(3)
)
ENGINE = ReplacingMergeTree(entered_at)
ORDER BY (field_id, year)
SETTINGS index_granularity = 8192;

CREATE TABLE agrocycle.indicator_lineage
(
    `indicator_id` String,
    `label` String,
    `source_ids` Array(LowCardinality(String)),
    `variables` Array(String),
    `formula` String,
    `aggregation_window` String,
    `spatial_support` String,
    `scale` Enum8('field' = 1, 'grid' = 2, 'regional' = 3, 'county' = 4, 'site' = 5),
    `resolution` String,
    `evidence_type` Enum8('observed' = 1, 'derived' = 2, 'classified' = 3, 'survey' = 4, 'model_reanalysis' = 5, 'experimental' = 6, 'published' = 7, 'assumption' = 8),
    `missing_data_rule` String,
    `interpretation` String,
    `limitation` String,
    `code_version` String,
    `run_id` String,
    `loaded_at` DateTime64(3, 'UTC') DEFAULT now64(3)
)
ENGINE = ReplacingMergeTree(loaded_at)
ORDER BY indicator_id
SETTINGS index_granularity = 8192;

CREATE TABLE agrocycle.marsden_management
(
    `rotation` Enum8('2yr' = 2, '3yr' = 3, '4yr' = 4),
    `metric` LowCardinality(String),
    `value` Float64,
    `unit` LowCardinality(String),
    `period` String,
    `evidence_type` Enum8('observed' = 1, 'derived' = 2, 'classified' = 3, 'survey' = 4, 'model_reanalysis' = 5, 'experimental' = 6, 'published' = 7, 'assumption' = 8) DEFAULT 'experimental',
    `source_id` LowCardinality(String),
    `indicator_id` String,
    `run_id` String,
    `loaded_at` DateTime64(3, 'UTC') DEFAULT now64(3)
)
ENGINE = ReplacingMergeTree(loaded_at)
ORDER BY (rotation, metric)
SETTINGS index_granularity = 8192;

CREATE TABLE agrocycle.ndvi_observations
(
    `field_id` String,
    `date` Date,
    `sensor` LowCardinality(String),
    `granule_id` String,
    `ndvi_mean` Nullable(Float32),
    `ndvi_p10` Nullable(Float32),
    `ndvi_p90` Nullable(Float32),
    `valid_pixels` UInt32,
    `total_pixels` UInt32,
    `passes_quality` Bool,
    `run_id` String,
    `loaded_at` DateTime64(3, 'UTC') DEFAULT now64(3)
)
ENGINE = ReplacingMergeTree(loaded_at)
ORDER BY (field_id, date, sensor, granule_id)
SETTINGS index_granularity = 8192;

CREATE TABLE agrocycle.pipeline_runs
(
    `run_id` String,
    `git_sha` String,
    `config_json` String,
    `input_checksums` Map(String, String),
    `started_at` DateTime64(3, 'UTC'),
    `finished_at` Nullable(DateTime64(3, 'UTC')),
    `status` Enum8('running' = 1, 'succeeded' = 2, 'failed' = 3)
)
ENGINE = ReplacingMergeTree(started_at)
ORDER BY run_id
SETTINGS index_granularity = 8192;

CREATE TABLE agrocycle.soil_properties
(
    `field_id` String,
    `mukey` String,
    `mu_name` String,
    `share_pct` Float32,
    `property` LowCardinality(String),
    `value_num` Nullable(Float64),
    `value_text` Nullable(String),
    `unit` LowCardinality(String),
    `indicator_id` String,
    `run_id` String,
    `loaded_at` DateTime64(3, 'UTC') DEFAULT now64(3)
)
ENGINE = ReplacingMergeTree(loaded_at)
ORDER BY (field_id, mukey, property)
SETTINGS index_granularity = 8192;
