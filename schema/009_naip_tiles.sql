-- Phase 12: an index of the NAIP image chips held in S3 (PRD S11): one row per field and source tile. The
-- images stay in S3; this table says which chip belongs to which field, when it was flown, and its checksum.
-- A field cut from two tiles has two rows, each with its own flight date. NAIP is reference imagery from a
-- single date per tile, never crop ground truth.
CREATE TABLE IF NOT EXISTS naip_tiles (
    field_id String,
    year UInt16,
    tile_id String,
    flight_date Date,
    resolution_m Float32,
    bbox_min_lon Float64,
    bbox_min_lat Float64,
    bbox_max_lon Float64,
    bbox_max_lat Float64,
    buffer_m Float32,
    bands LowCardinality(String),
    s3_key String,
    size_bytes UInt64,
    sha256 FixedString(64),
    retrieval_date Date,
    evidence_type Enum8('observed' = 1, 'derived' = 2, 'classified' = 3, 'survey' = 4,
                        'model_reanalysis' = 5, 'experimental' = 6, 'published' = 7, 'assumption' = 8),
    source_id LowCardinality(String),
    load_id String
) ENGINE = MergeTree
PARTITION BY tuple()
ORDER BY (field_id, year, tile_id);
