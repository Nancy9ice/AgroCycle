-- F1: Ask AgroCycle — Q&A log. Every question and answer is stored for the Phase 15 claim check.
-- context_type: 'analysis' = called from the compare/saved-result screen;
--               'field'    = called from the profile screen.
CREATE TABLE IF NOT EXISTS ask_log (
    log_id       String,
    context_type Enum8('analysis' = 1, 'field' = 2),
    context_id   String,                    -- analysis_id or field_id
    field_id     String,
    question     String,
    answer       String,
    citations    Array(String),             -- indicator_ids cited
    refused      UInt8,                     -- 1 = refused (out-of-scope question)
    audience     LowCardinality(String),    -- 'farmer' | 'adviser'
    model        LowCardinality(String),
    created_at   DateTime64(3, 'UTC') DEFAULT now64(),
    load_id      String
) ENGINE = MergeTree
PARTITION BY toYYYYMM(created_at)
ORDER BY (created_at, log_id);
