-- Stored compare responses. Each row is one POST /fields/{id}/compare result.
-- response_json holds the full CompareResponse payload so GET /analyses/{id} returns it byte-for-byte.
CREATE TABLE IF NOT EXISTS analyses (
    analysis_id String,
    field_id String,
    created_at DateTime64(3, 'UTC') DEFAULT now64(),
    engine_version String,
    data_version String,
    response_json String,
    load_id String
) ENGINE = MergeTree
PARTITION BY toYYYYMM(created_at)
ORDER BY (created_at, analysis_id);
