-- Feedback from farmers, advisers and researchers (POST /feedback). One row per submission, append only.
-- farming_context says who is speaking (for example "Nigerian farmer, usability review" or "Iowa adviser") so
-- feedback that cannot speak to Iowa agronomy is never mixed up with feedback that can.
-- contact is personal data: it is stored only when contact_consent is 1, and is empty otherwise.
CREATE TABLE IF NOT EXISTS feedback (
    feedback_id String,
    created_at DateTime64(3, 'UTC') DEFAULT now64(3),
    role LowCardinality(String),
    farming_context String,
    usefulness UInt8,
    clarity UInt8,
    what_was_missing String,
    would_use LowCardinality(String),
    contact String,
    contact_consent UInt8,
    field_id String,
    analysis_id String,
    load_id String DEFAULT 'api'
) ENGINE = MergeTree
PARTITION BY toYYYYMM(created_at)
ORDER BY (created_at, feedback_id);
