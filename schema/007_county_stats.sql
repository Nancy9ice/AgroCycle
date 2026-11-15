-- Phase 12: NASS QuickStats county statistics (Story and Boone, Iowa), as published. County context only, never
-- field-level yield validation (PRD S12). One row per county, commodity, class, utilization, statistic, unit and
-- year. A withheld value, "(D)" in the source, is NULL with value_status 'withheld': it is never filled or zeroed.
-- Corn has two utilizations (GRAIN in bushels, SILAGE in tons); hay has three classes (ALFALFA, EXCL ALFALFA, ALL).
CREATE TABLE IF NOT EXISTS county_stats (
    county LowCardinality(String),
    county_fips FixedString(5),
    year UInt16,
    commodity LowCardinality(String),
    class_desc LowCardinality(String),
    utilization LowCardinality(String),
    statistic LowCardinality(String),
    unit LowCardinality(String),
    value Nullable(Float64),
    value_status Enum8('reported' = 1, 'withheld' = 2),
    cv_percent Nullable(Float64),
    short_desc String,
    evidence_type Enum8('observed' = 1, 'derived' = 2, 'classified' = 3, 'survey' = 4,
                        'model_reanalysis' = 5, 'experimental' = 6, 'published' = 7, 'assumption' = 8),
    source_id LowCardinality(String),
    load_id String
) ENGINE = MergeTree
PARTITION BY tuple()
ORDER BY (county, commodity, class_desc, utilization, statistic, unit, year);
