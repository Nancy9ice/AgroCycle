# Plan: Analysis-ready HLS: mask, scaling and valid-pixel counts

- **Role:** de
- **Spec created:** 2026-11-15
- **Roadmap phase and task:** Phase 5, DE: prepare analysis-ready HLS (clip, quality mask), with the valid-observation counts DS1 needs

## Goal
Give DS1 one tested function that returns masked, scaled HLS reflectance for a field and date, and load a table of valid-pixel counts per field, sensor and date, so every HLS value she computes has its denominator. NDVI, zonal statistics, bare-field windows and the HLS-versus-CDL test stay with DS1.

## Approach
- **Function plus counts table** (decision 2026-11-15): no masked rasters are stored. The function reads a stack from the local pull or S3 and masks it on demand; only the counts are loaded.
- **The DE masks** (decision 2026-11-15, the roadmap's reading). DS1's sheet says she masks; the DE tells her that point is superseded, and gives her the corrected bit rule: a pixel is kept only if `Fmask & 0b00111110 == 0` (bits 1-5: cloud, adjacent to cloud, shadow, snow/ice, water), and fill (`Fmask == 255`) is never kept.
- Counts use the pixels whose centre lies in the field polygon, the rule Phase 3 uses for CDL.
- One row per window, so the 14,598 uploaded stacks and the 1,962 windows with no data (status `no_data`, valid 0) are all accounted for: 16,560 rows.
- Dry run by default; `--load` writes.

## Task groups

### 1. Claim and branch
1. Set the Phase 5 DE row to `In progress`. Branch from `origin/main`. Done.

### 2. Mask and scaling
1. `transform/hls/mask.py`: the Fmask rule, fill to null, reflectance x 0.0001, and the field-polygon clip; one function returning masked float32 bands.
2. Tests: all 256 Fmask values against the rule, the bit boundaries, fill, and the committed primary-001 sample scenes.

### 3. Counts per window
1. `transform/hls/counts.py`: total, fill, flagged and valid pixels per window; status `no_data` when the window is all fill.
2. `transform/hls/sources.py`: list and read the stacks from the local pull (`HLS_DIR`) or S3; read `skipped_no_data.csv` for windows with no file.

### 4. Table and schema
1. `schema/004_hls_valid_pixels.sql` and the Pandera schema in `common/schemas.py` (`valid + flagged + fill = total`, no-data rows have zero valid pixels).

### 5. Runner
1. `python -m transform.hls.run` (dry run) and `--load`; a local CSV copy in `data/out/hls/`.

### 6. Validation and close
1. Independent recount, idempotent load, DS1 review; results, tracker, `/code-review`, PR.

## Files, tables and endpoints
- New: `transform/hls/{mask,counts,sources,run}.py`, `schema/004_hls_valid_pixels.sql`, tests.
- Changed: `common/schemas.py`, `specs/roadmap.md` (own row).
- ClickHouse: `hls_valid_pixels` (new).

## Dependencies and interfaces
- **DS1:** calls `masked_reflectance`; reads `hls_valid_pixels` for her denominators and valid-observation counts; her sheet's masking and bit table are superseded and she must be told.
- **BE and FE (Phase 13):** NDVI timelines with valid-observation markers read `hls_valid_pixels`.
- **Phase 1:** the stacks in S3 and `raw/hls/no-data/.../skipped_no_data.csv`.

## Data size
About 16,560 rows. The stacks are already local (210 MB) and in S3.

## Risks and open questions
- The stacks store `Fmask` as int16 holding the 0-255 source values; the rule is applied to those values unchanged.
- Two granules can fall on one day (Sentinel-2); the key includes the sensing time.
- The 460 first-pull files (primary-001, 2023, one file per band) are a different layout and are not used; the full run covers the same field and year.
- Without the local pull, the 1,962 no-data windows have no file in S3, so their pixel totals come from the polygon and the grid of a sibling stack.
- `Fmask` is a model-based quality flag, not ground truth; bits 6-7 (aerosol level) are not used in the mask.
