-- Phase 2 core tables. Applied by `python -m common.migrate`; never edit once applied, add 002_*.sql.
-- Every table carries load_id (the run that wrote the row). Loads swap whole partitions
-- (common/load.py), so each partition key is the unit a reload replaces.

-- One row per raw file or product, from the Phase 1 manifests. A reload replaces one source.
CREATE TABLE IF NOT EXISTS data_sources (
    source_id LowCardinality(String),
    s3_key String,
    source_url String,
    product String,
    version String,
    retrieval_date Date,
    sha256 FixedString(64),
    size_bytes UInt64,
    licence LowCardinality(String),
    subset String,
    evidence_type Enum8('observed' = 1, 'derived' = 2, 'classified' = 3, 'survey' = 4,
                        'model_reanalysis' = 5, 'experimental' = 6, 'published' = 7, 'assumption' = 8),
    scale LowCardinality(String),
    notes String,
    load_id String
) ENGINE = MergeTree
PARTITION BY source_id
ORDER BY (source_id, version, retrieval_date, s3_key);

-- One row per derived indicator. The 15 columns before load_id are DS2's contract
-- (transform/indicators/runner.py). A reload replaces one code_version.
CREATE TABLE IF NOT EXISTS indicator_lineage (
    indicator_id String,
    label String,
    source_ids String,
    variables String,
    formula String,
    aggregation_window String,
    spatial_support String,
    scale LowCardinality(String),
    resolution String,
    evidence_type Enum8('observed' = 1, 'derived' = 2, 'classified' = 3, 'survey' = 4,
                        'model_reanalysis' = 5, 'experimental' = 6, 'published' = 7, 'assumption' = 8),
    missing_data_rule String,
    interpretation String,
    limitation String,
    code_version LowCardinality(String),
    run_id String,
    load_id String
) ENGINE = MergeTree
PARTITION BY code_version
ORDER BY (indicator_id, code_version);

-- The demo fields. Small, always reloaded whole.
CREATE TABLE IF NOT EXISTS fields (
    field_id String,
    role Enum8('primary' = 1, 'test' = 2),
    boundary_source Enum8('demo' = 1, 'real' = 2),
    county LowCardinality(String),
    provenance String,
    domain_note String,
    cover_detail String,
    geometry_wkt String,
    load_id String
) ENGINE = MergeTree
PARTITION BY tuple()
ORDER BY field_id;
