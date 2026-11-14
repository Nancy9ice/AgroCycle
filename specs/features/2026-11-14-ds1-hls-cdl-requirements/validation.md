# Validation: HLS and CDL source requirements sheet

## Checks

| Requirement / criterion | How it will be verified | Evidence kept |
|---|---|---|
| Completeness (all 10 sections) | Manual review of each sheet against the requirements.md checklist | Screenshot or note in this table |
| Clarity (DE can implement without asking) | Self-review: read each instruction and ask "Would a DE need to clarify anything?" | Notes on any ambiguous sections that were revised |
| Size budget defined | Check sheet contains explicit MB/field and total estimate | Value recorded in results |
| Provenance fields specified | Check sheet lists all manifest fields | Confirmed in results |
| Validity check defined | Check sheet contains a specific validation procedure for first file | Confirmed in results |

## Results (fill in after implementation)

- **Date completed:** 2026-11-14
- **What was run:** Manual self-review of both requirements sheets
- **Passed:**
  - ✅ **HLS sheet (hls-requirements-sheet.md):**
    - All 10 sections: present (Product/version, Access, Spatial, Temporal, Bands, Quality, Output format, Size budget, Manifest, Validation check)
    - Size budget: ~50 MB dev sample, ~5–15 GB full set
    - Manifest: all fields specified (URL, version, retrieval date, SHA-256, size, licence)
    - Validation check: 7-point procedure defined for first pull
  - ✅ **CDL sheet (cdl-requirements-sheet.md):**
    - All 10 sections: present
    - Size budget: ~10 KB dev sample, ~5–30 MB full set
    - Manifest: all fields specified including resolution per year
    - Validation check: 7-point procedure defined for first pull
  - ✅ Both sheets include explicit size budgets
  - ✅ Both sheets define manifest provenance fields
  - ✅ Both sheets define a one-file validation check the DS will run
  - ✅ HLS sheet specifies Fmask values and the cloud/shadow/snow/water mask logic
  - ✅ CDL sheet specifies the 30 m → 10 m resolution change from 2024 and the need to record it
- **Failed or skipped:** None
- **Evidence location:**
  - `specs/features/2026-11-14-ds1-hls-cdl-requirements/hls-requirements-sheet.md`
  - `specs/features/2026-11-14-ds1-hls-cdl-requirements/cdl-requirements-sheet.md`
  - `specs/features/2026-11-14-ds1-hls-cdl-requirements/plan.md`
  - `specs/features/2026-11-14-ds1-hls-cdl-requirements/requirements.md`
  - `specs/features/2026-11-14-ds1-hls-cdl-requirements/validation.md`
- **Roadmap exit check met:** The Phase 1 exit check ("each source has its raw files in S3 with a manifest and a verified checksum") requires DE extraction; these sheets are the DS prerequisite. The sheets are complete and ready for DE handoff.
- **Roadmap tracker updated:** Yes, 2026-11-14