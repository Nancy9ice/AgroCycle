-- Phase 5: NDVI time series per field per window. One row per valid window where NDVI could be computed.
-- NDVI = (NIR - Red) / (NIR + Red) from HLS L30/S30 masked reflectance, scaled 0.0001.
-- Recomputed whole, one partition. The frontend reads this to show vegetation timelines.
CREATE TABLE IF NOT EXISTS hls_ndvi (
    field_id String,
    sensor LowCardinality(String),
    acquired Date,
    sensing_time String,
    ndvi_mean Float32,
    ndvi_median Float32,
    ndvi_p25 Float32,
    ndvi_p75 Float32,
    ndvi_std Float32,
    ndvi_valid_pixels UInt32,
    valid_share Float32,
    n_clear_pixels UInt32,
    load_id String
) ENGINE = MergeTree
PARTITION BY tuple()
ORDER BY (field_id, acquired, sensor, sensing_time);