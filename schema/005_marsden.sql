-- Phase 6: DS2's Marsden Farm reproduction (Davis et al. 2012), loaded by the DE. Experimental evidence from one
-- research site, treatment-level values. Each is recomputed whole, so each is one partition.

-- One row per rotation, period and metric. A by-year row has first_year = last_year; the nine-year mean has
-- 2003 and 2011. applied_n = manufactured_n + manure_n; applied N excludes biological N fixation. indicator_id
-- links every row to its indicator_lineage row.
CREATE TABLE IF NOT EXISTS marsden_management (
    rotation Enum8('2-yr' = 1, '3-yr' = 2, '4-yr' = 3),
    first_year UInt16,
    last_year UInt16,
    metric LowCardinality(String),
    indicator_id String,
    value Float64,
    unit LowCardinality(String),
    n_years UInt8,
    evidence_type Enum8('observed' = 1, 'derived' = 2, 'classified' = 3, 'survey' = 4,
                        'model_reanalysis' = 5, 'experimental' = 6, 'published' = 7, 'assumption' = 8),
    source_id LowCardinality(String),
    load_id String
) ENGINE = MergeTree
PARTITION BY tuple()
ORDER BY (rotation, metric, first_year, last_year);

-- DS2's reconciliation of the reproduction with the PRD targets and the paper's own text. One check is
-- UNRECONCILED by design (2-yr manufactured N, 74.5 from Table S3 against 80 in the text): it stays visible.
-- rotation is text because some checks cover "3-yr & 4-yr" or carry a diagnostic note.
CREATE TABLE IF NOT EXISTS marsden_reconciliation (
    quantity String,
    rotation String,
    computed Float64,
    reference Float64,
    source String,
    rule String,
    status Enum8('MATCH' = 1, 'WITHIN_SEM' = 2, 'UNRECONCILED' = 3, 'INFO' = 4),
    note String,
    load_id String
) ENGINE = MergeTree
PARTITION BY tuple()
ORDER BY (quantity, rotation, source);
