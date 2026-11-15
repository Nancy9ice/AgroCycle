# Requirements: Fill data_sources and link every output to its source

## Covers
- **PRD requirements:** §6.1 (record, for each source, provider, product and version, URL, variables, resolutions, coverage, retrieval date, licence, processing steps, quality flags, limitations), FR-12 (traceability), NFR-03 (auditability), NFR-02 (explainability).
- **Roadmap exit check satisfied:** Phase 2's "link every indicator row to both" `data_sources` and `indicator_lineage` (tech-stack, ClickHouse modelling).

## Decisions (2026-11-15)
- One row per source pull; file detail stays in the S3 manifests.
- `data_sources` is reshaped by migration 006 (it was empty and unread).
- The DE compiles the PRD 6.1 text; DS1 and DS2 review it.
- Links: every indicator, and the crop-history, HLS, climate, soil and Marsden tables. A per-file inventory is out.
- Validation: golden tests plus a live check against S3.

## Inputs
- The S3 manifests and objects under `raw/`: `cdl`, `hls/l30`, `hls/s30`, `hls/no-data`, `power`, `ssurgo`, `marsden`.
- `indicator_lineage.source_ids` (JSON text of a source name) for the 25 indicators.
- DS1's and DS2's source sheets and the Phase 1 to 6 specs, for the compiled text.

## Outputs

| Table | Rows | Columns |
|---|---|---|
| `data_sources` | 8 | source_id, provider, product, product_version, url, variables (JSON text), spatial_resolution, temporal_resolution, geographic_coverage, historical_coverage, retrieval_date, licence, processing_steps, quality_flags, known_limitations, evidence_type, raw_s3_prefix, file_count, total_bytes, compiled_from, load_id |
| `source_links` | about 40 | subject_type (`indicator` or `table`), subject_id, source_id, load_id |

`source_id` values: `cdl`, `hls_l30`, `hls_s30`, `hls_no_data`, `power`, `ssurgo`, `marsden_supplement`, `marsden_europepmc`.

## Acceptance criteria
1. Every source row has every PRD 6.1 field non-empty (variables a non-empty list), and `compiled_from` names where the text came from.
2. `product`, `retrieval_date`, `licence` and `evidence_type` equal what the pull's S3 manifest says; `file_count` and `total_bytes` equal an independent recount of the S3 objects; every prefix under `raw/` is covered by exactly one source.
3. Every indicator in `indicator_lineage` is linked to at least one source, by its `source_ids` text; a text the catalog does not know fails the build and names the indicator.
4. Every link names a source that exists, and every `indicator` link names an indicator that exists. `crop_class_shares`, `crop_history`, `crop_rotation` and `fields` link to `cdl`; `hls_valid_pixels` to the HLS sources; `climate_points` and `climate_daily` to `power`; `soil_properties` to `ssurgo`; the Marsden tables to `marsden_supplement`.
5. The migration drops the old per-file `data_sources` only when it is empty; the runner refuses otherwise. The migration runner still works with a table prefix.
6. Loads are idempotent (identical table hashes); `make check` passes without S3 or ClickHouse (live checks skip).

## Evidence labels, scale and limitations to preserve
- Each source keeps the manifest's evidence type (observed, classified, model_reanalysis, survey, experimental, derived) and states its scale and limits in its own words, for example POWER's grid scale and CDL's "agreement, not validation".
- The text is compiled by the DE and not yet reviewed by DS1 and DS2; `compiled_from` says so.

## Out of scope
A per-file inventory, new sources (NASS, AMS, NAIP, PRISM, SMAP/GPM, Phase 12), changing any lineage text, and the API and page that show the links.
