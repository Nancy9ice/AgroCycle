-- Phase 5: the valid-pixel counts behind every HLS value. One row per stacked window (a field, a sensor, an
-- acquisition date and a sensing time). Pixels are those whose centre lies in the field polygon, and each is
-- exactly one of fill, flagged or valid, so total = fill + flagged + valid. A window with no data is
-- status 'no_data' with zero valid pixels: it is no observation, never clear. Recomputed whole, one partition.
CREATE TABLE IF NOT EXISTS hls_valid_pixels (
    field_id String,
    sensor LowCardinality(String),
    acquired Date,
    sensing_time String,
    status Enum8('observed' = 1, 'no_data' = 2),
    total_pixels UInt32,
    fill_pixels UInt32,
    flagged_pixels UInt32,
    valid_pixels UInt32,
    valid_share Float32,
    mask_rule LowCardinality(String),
    source_s3_key String,
    load_id String
) ENGINE = MergeTree
PARTITION BY tuple()
ORDER BY (field_id, acquired, sensor, sensing_time);
