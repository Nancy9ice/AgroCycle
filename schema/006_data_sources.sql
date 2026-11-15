-- Source provenance (PRD 6.1, FR-12). data_sources was created in 001 as one row per raw file and was never
-- filled: it holds no rows and nothing reads it. It becomes one row per source pull, with the fields the PRD
-- asks for; the per-file detail stays in the manifests beside the objects in S3. The loader refuses to
-- run this migration over a table that holds rows.
DROP TABLE IF EXISTS data_sources;

CREATE TABLE IF NOT EXISTS data_sources (
    source_id LowCardinality(String),
    provider String,
    product String,
    product_version String,
    url String,
    variables String,
    spatial_resolution String,
    temporal_resolution String,
    geographic_coverage String,
    historical_coverage String,
    retrieval_date Date,
    licence String,
    processing_steps String,
    quality_flags String,
    known_limitations String,
    evidence_type Enum8('observed' = 1, 'derived' = 2, 'classified' = 3, 'survey' = 4,
                        'model_reanalysis' = 5, 'experimental' = 6, 'published' = 7, 'assumption' = 8),
    raw_s3_prefix String,
    file_count UInt32,
    total_bytes UInt64,
    compiled_from String,
    load_id String
) ENGINE = MergeTree
PARTITION BY tuple()
ORDER BY source_id;

-- Which sources stand behind an indicator, or behind a derived table. An indicator link is built from the
-- source text in indicator_lineage; a table link says which pulls a table was computed from.
CREATE TABLE IF NOT EXISTS source_links (
    subject_type Enum8('indicator' = 1, 'table' = 2),
    subject_id String,
    source_id LowCardinality(String),
    load_id String
) ENGINE = MergeTree
PARTITION BY tuple()
ORDER BY (subject_type, subject_id, source_id);
