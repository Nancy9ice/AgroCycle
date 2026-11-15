-- Phase 4 tables: cleaned POWER climate and DS2's indicators. Each is recomputed whole, so each is one partition
-- and a reload replaces it atomically (common/load.py). The column names and order of field_indicators and
-- soil_properties are the ones DS2's runner writes, so his CSVs load without a change.

-- DS2's indicator values: one row per field, indicator and season window (soil indicators have no window).
-- A null value is "unknown", never zero; the status and reason say why.
CREATE TABLE IF NOT EXISTS field_indicators (
    field_id String,
    indicator_id String,
    category Enum8('climate' = 1, 'soil' = 2, 'vegetation' = 3, 'water' = 4, 'regional' = 5, 'context' = 6),
    value Nullable(Float64),
    unit LowCardinality(String),
    status Enum8('available' = 1, 'partial' = 2, 'unknown' = 3, 'not_assessed' = 4),
    window_start Nullable(Date),
    window_end Nullable(Date),
    valid_obs Nullable(UInt32),
    unknown_reason Nullable(String),
    run_id String,
    load_id String
) ENGINE = MergeTree
PARTITION BY tuple()
ORDER BY (field_id, indicator_id);

-- The soil behind the indicators: map-unit shares and class shares (drainage, hydrologic group). mukey is empty
-- for the class rows.
CREATE TABLE IF NOT EXISTS soil_properties (
    field_id String,
    mukey String,
    mu_name String,
    share_pct Nullable(Float32),
    property LowCardinality(String),
    value_num Nullable(Float64),
    value_text Nullable(String),
    unit LowCardinality(String),
    indicator_id String,
    run_id String,
    load_id String
) ENGINE = MergeTree
PARTITION BY tuple()
ORDER BY (field_id, property, mukey);

-- Which climate cell each point (a field, or the Marsden site) reads. Cells are found by identical content,
-- because the POWER API returns the coordinates it was sent, not a grid-cell centre. Grid scale, not field.
CREATE TABLE IF NOT EXISTS climate_points (
    point_id String,
    cell_id String,
    latitude Float64,
    longitude Float64,
    elevation_m Float64,
    load_id String
) ENGINE = MergeTree
PARTITION BY tuple()
ORDER BY point_id;

-- Cleaned daily POWER, one series per cell. value is null where the source held the fill value (-999) or had
-- no row; qc_flag says which. Units are those of the response.
CREATE TABLE IF NOT EXISTS climate_daily (
    cell_id String,
    variable LowCardinality(String),
    date Date,
    value Nullable(Float32),
    unit LowCardinality(String),
    qc_flag LowCardinality(String),
    load_id String
) ENGINE = MergeTree
PARTITION BY tuple()
ORDER BY (cell_id, variable, date);
