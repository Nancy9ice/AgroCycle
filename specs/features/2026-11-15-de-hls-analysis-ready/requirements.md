# Requirements: Analysis-ready HLS: mask, scaling and valid-pixel counts

## Covers
- **PRD requirements:** FR-04 (vegetation and bare-field windows, data adequacy), FR-06, NFR-01, NFR-03.
- **Roadmap exit check satisfied (DE part):** "HLS features loaded with denominators and passing checks." The features are DS1's; the denominators are this phase.

## Decisions (2026-11-15)
- Scope: the Fmask mask with scaling and the polygon clip; valid-pixel counts per field and date; the counts loaded into ClickHouse. NDVI zonal statistics are out (DS1).
- The DE applies the mask; DS1 builds features. DS1's sheet ("masking is DS1's task") is superseded on this point.
- Output is a function plus a counts table; no masked rasters are stored.
- Validation: offline golden tests plus a live recount that skips without the stacks.

## Inputs
- The 14,598 stacked windows in `s3://<bucket>/raw/hls/{l30,s30}/v2.0/2026-11-14/<field>/<YYYYMMDD>/T<hhmmss>_stack_*.tif`, or the same files under `~/agrocycle_hls/stacks` (`HLS_DIR`). Int16, EPSG:32615, 30 m, the field window plus a 500 m buffer. Bands in order: L30 `B04, B05, B06, Fmask`; S30 `B04, B8A, B11, Fmask`. Reflectance scale 0.0001, fill -9999; `Fmask` holds the 0-255 source value, 255 is fill.
- `raw/hls/no-data/v2.0/2026-11-14/skipped_no_data.csv`: the 1,962 windows with no data.
- `data/fields/fields.geojson` for the polygons.

## Outputs
- `masked_reflectance(stack, polygon) -> float32 bands, NaN where masked, filled or outside the polygon`, in physical reflectance (x 0.0001).
- Table `hls_valid_pixels`, one row per window (16,560):

| Column | Meaning |
|---|---|
| field_id, sensor (`l30`/`s30`), acquired (date), sensing_time (`Thhmmss`) | the key |
| status | `no_data` when every pixel of the field is fill (no observation, even if the window's buffer holds data); otherwise `observed` |
| total_pixels | pixels whose centre is in the polygon |
| fill_pixels | no data in the source (`Fmask == 255` or a band at -9999) |
| flagged_pixels | cloud, adjacent to cloud, shadow, snow/ice or water, and not fill |
| valid_pixels | kept by the mask rule |
| valid_share | `valid_pixels / total_pixels` |
| mask_rule | the rule text, so a change of rule is visible in the data |
| source_s3_key | the stack in S3; for the 1,962 windows that were all fill and never uploaded, the key of `skipped_no_data.csv` |
| load_id | provenance |

## Acceptance criteria
1. The mask rule is tested for all 256 `Fmask` values: a pixel is valid exactly when `Fmask & 0b00111110 == 0` and `Fmask != 255`; bits 0, 6 and 7 never mask.
2. Fill becomes null, never zero; reflectance is scaled by 0.0001 and otherwise unchanged; pixels outside the polygon are null.
3. For every window, `valid + flagged + fill = total`, `valid_share` agrees, and `status` is `no_data` exactly when `fill = total` (then `valid = 0`).
4. All 16,560 windows appear once: 14,496 `observed` and 2,064 `no_data`. The 1,962 windows Phase 1 listed are all `no_data` and keyed to the list; the other 102 are stacks whose data stops short of the field.
5. Counts agree with an independent recount (shapely pixel centres and plain bitwise arithmetic) for every window of the primary and 5 sample fields, and on the committed primary-001 sample scenes.
6. The frame passes Pandera before the load; the load goes through `common.load`; a second run gives identical table hashes.
7. `make check` passes without S3 or ClickHouse access.

## Evidence labels, scale and limitations to preserve
- `observed`, 30 m, surface reflectance. `Fmask` is a model-based quality flag, not ground truth; the aerosol bits are not used.
- A count describes the pixels in the polygon, not the whole window. Edge pixels move a share by a point or two.
- A window with no data over the field is "no observation", never clear or cloudy. Found on the real data by the code review: 102 stored windows have data in the buffer but none over the field, so `no_data` is decided at the field, not the window.

## Out of scope
NDVI and its statistics, bare-field windows, the HLS-versus-CDL test, any change to the stacks in S3, the SWIR use, and the API.
