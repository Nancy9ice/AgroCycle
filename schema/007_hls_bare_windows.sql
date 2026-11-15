-- Phase 5: bare-field windows derived from HLS NDVI time series.
-- A bare window is a period >= 14 consecutive days where field NDVI < 0.3 (no actively growing crop).
-- Confidence: high = first bare window of the year, low = second window (unusual).
CREATE TABLE IF NOT EXISTS hls_bare_windows (
    field_id String,
    year UInt16,
    bare_window_start Date,
    bare_window_end Date,
    bare_days UInt16,
    ndvi_before Nullable(Float32),
    ndvi_after Nullable(Float32),
    confidence Enum8('high' = 1, 'medium' = 2, 'low' = 3),
    load_id String
) ENGINE = MergeTree
PARTITION BY tuple()
ORDER BY (field_id, year, bare_window_start);