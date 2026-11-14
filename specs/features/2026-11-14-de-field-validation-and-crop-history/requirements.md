# Requirements: Field validation and crop history

## Covers
- **PRD requirements:** FR-01 (field validation), FR-02 (crop history), FR-06 (data adequacy), NFR-01 (reproducibility), NFR-03 (auditability).
- **Roadmap exit check satisfied:** "the crop-history table for the primary and test fields passes schema checks, is loaded in ClickHouse and is served by the API" (the serving is BE's).

## Decisions (2026-11-14)
- Scope: field validation and `fields` load, CDL clip and class shares, DS1's rules v1.0, Pandera and the ClickHouse load. Not in scope: serving through the API (BE).
- The DE clips (roadmap), not DS1. To be confirmed with her.
- The 5 fields that become continuous corn are kept and labelled by the rules.
- Validation: offline golden tests plus a live recompute that skips without the raw clips.
- Stacked on nothing: PR #12 is merged.

## Inputs
- CDL county clips 2015-2025 and class tables from the Phase 1 pull folder (`~/agrocycle_cdl`; the same files are in `s3://<bucket>/raw/cdl/annual-30m-website-export/2026-11-14/`), 30 m, EPSG:5070; 2024-2025 resampled from 10 m.
- `data/fields/fields.geojson` (45 fields: 1 primary, 44 test; all demo geometry).
- DS1's `specs/features/2026-11-14-ds1-cdl-crop-history-rules/cdl-crop-rules.md`, v1.0.

## Outputs

| Table | Rows | Columns |
|---|---|---|
| `fields` | 45 | the Phase 2 columns: field_id, role, boundary_source (`demo`), county, provenance, domain_note, cover_detail, geometry_wkt, load_id |
| `crop_class_shares` | per field, year, class | field_id, year, cdl_class_code, cdl_class_name, class_group, flag (`unlisted_code` or empty), pixels, share_pct, resolution_m, product_version, source_s3_key, load_id |
| `crop_history` | per field, year | field_id, year, dominant_group, status (`ok`, `mixed_uncertain`, `low_confidence`), dominant_share_pct, nodata_share_pct, total_pixels, rule_version, evidence_type (`classified`), load_id |
| `crop_rotation` | per field | field_id, field_class (`rotation`, `continuous_corn`, `pasture_hay`, `mixed`, `other`), sequence, corn_years, soybean_years, pasture_hay_years, alternations, transitions_counted, rule_version, evidence_type (`derived`), limitation, load_id |

Shares are percentages of pixels whose centre lies in the polygon; no-data (code 0) counts toward the total. Sequence letters: C corn, S soybeans, O oats, A alfalfa, P pasture/hay, N non-crop, X other crop, M mixed/uncertain, L low-confidence.

## Acceptance criteria
1. Every field passes `validate_fields` (valid, non-empty, inside its county) and loads into `fields` with a role and `boundary_source`.
2. For each field and year 2015-2025, shares sum to 100 % (within rounding) and agree with an independent recompute from the raw clip for the primary and 5 sample fields.
3. Rules reproduce DS1's example: primary-001 is `S C S C S C S C S C S`, 10 of 10 alternations, `rotation`.
4. A year with no group at 60 % is `mixed_uncertain`; no-data above 20 % is `low_confidence` and is left out of the rotation count. Boundaries at exactly 60 % and 20 % are tested.
5. Rule order is rotation, continuous corn, pasture/hay, mixed, other. Boundaries at 7 of 10 and 8 of 11 are tested.
6. Every `crop_history` and `crop_rotation` row carries `rule_version`, resolution and product version trace to the source clip, and a limitation is stated.
7. Unknown or unexpected class codes become `other-crop` and are flagged, never raise.
8. Frames pass Pandera before the load; loads go through `common.load`; running the load twice leaves identical table hashes.
9. `make check` passes without S3 or ClickHouse access (live checks skip); the SQL and schemas agree.
10. The 5 continuous-corn fields are labelled `continuous_corn` and listed in the validation record for DS1.

## Evidence labels, scale and limitations to preserve
- CDL shares: `classified`, 30 m. A classified product, not ground truth; 2024-2025 resampled from 10 m.
- Dominant crop and rotation class: `derived` from CDL, field scale. They carry the CDL's accuracy and DS1's thresholds, which are not expert-reviewed.
- Demo geometry: not real farm boundaries.
- Agreement with another classification is not validation (PRD §4.4).

## Out of scope
The API endpoint, HLS-based crop checks (Phase 5), strategy rules (Phase 9), accuracy assessment (Phase 14), and changing DS1's thresholds.
