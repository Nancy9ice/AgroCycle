-- Phase 3 crop-history tables. Each is recomputed whole from the CDL clips, so each is one partition
-- and a reload replaces it atomically (common/load.py). Every row carries load_id and rule_version.

-- CDL class shares per field and year: pixels whose centre lies in the polygon (no-data, code 0, included).
CREATE TABLE IF NOT EXISTS crop_class_shares (
    field_id String,
    year UInt16,
    cdl_class_code UInt16,
    cdl_class_name LowCardinality(String),
    class_group LowCardinality(String),
    flag LowCardinality(String),
    pixels UInt32,
    share_pct Float32,
    resolution_m UInt16,
    product_version String,
    source_s3_key String,
    load_id String
) ENGINE = MergeTree
PARTITION BY tuple()
ORDER BY (field_id, year, cdl_class_code);

-- One label per field and year, by DS1's section 2 (60 % dominant, no-data above 20 % low-confidence).
CREATE TABLE IF NOT EXISTS crop_history (
    field_id String,
    year UInt16,
    dominant_group LowCardinality(String),
    status Enum8('ok' = 1, 'mixed_uncertain' = 2, 'low_confidence' = 3),
    dominant_share_pct Float32,
    nodata_share_pct Float32,
    total_pixels UInt32,
    rule_version LowCardinality(String),
    evidence_type Enum8('observed' = 1, 'derived' = 2, 'classified' = 3, 'survey' = 4,
                        'model_reanalysis' = 5, 'experimental' = 6, 'published' = 7, 'assumption' = 8),
    load_id String
) ENGINE = MergeTree
PARTITION BY tuple()
ORDER BY (field_id, year);

-- One row per field: the sequence and the class from DS1's sections 3 to 7.
CREATE TABLE IF NOT EXISTS crop_rotation (
    field_id String,
    field_class Enum8('rotation' = 1, 'continuous_corn' = 2, 'pasture_hay' = 3, 'mixed' = 4, 'other' = 5),
    sequence String,
    corn_years UInt8,
    soybean_years UInt8,
    pasture_hay_years UInt8,
    alternations UInt8,
    transitions_counted UInt8,
    rule_version LowCardinality(String),
    evidence_type Enum8('observed' = 1, 'derived' = 2, 'classified' = 3, 'survey' = 4,
                        'model_reanalysis' = 5, 'experimental' = 6, 'published' = 7, 'assumption' = 8),
    limitation String,
    load_id String
) ENGINE = MergeTree
PARTITION BY tuple()
ORDER BY field_id;
