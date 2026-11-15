-- Boundaries a farmer drew themselves (POST /fields/drawn), and the crop history they told us.
-- One row per field_id; an update inserts a newer row and ReplacingMergeTree keeps the latest by updated_at
-- (read with FINAL). These are not pre-processed fields: they have no CDL, soil or weather, only what is here.
-- crop_sequence is the farmer's own answer (one letter per year from 2015, the web app's crop codes), never
-- CDL data. field_class is DS1's classification rules applied to that answer, empty until one is given.
CREATE TABLE IF NOT EXISTS drawn_fields (
    field_id String,
    name String,
    county LowCardinality(String),
    area_ha Float32,
    geometry String,
    crop_sequence String DEFAULT '',
    field_class LowCardinality(String) DEFAULT '',
    created_at DateTime64(3, 'UTC') DEFAULT now64(3),
    updated_at DateTime64(3, 'UTC') DEFAULT now64(3),
    load_id String DEFAULT 'api'
) ENGINE = ReplacingMergeTree(updated_at)
ORDER BY field_id;
