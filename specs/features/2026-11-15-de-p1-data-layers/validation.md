# Validation: P1 data layers (DE)

## Checks

| Requirement / criterion | How it will be verified | Evidence kept |
|---|---|---|
| 1. Decision recorded per layer | Read the tracker row and the sign-off note before each load | Tracker rows, `docs/source_requirements/de_p1_layers_draft.md` sign-off table |
| 2. No sign-off means nothing loaded | List `raw/<source>/` in S3 and count rows in the table for that layer | Listing and count in the results below |
| 3. Dropped layers recorded | Tracker rows for PRISM, SMAP/GPM and erosion | Tracker |
| 4. Size budget | Dry-run size report before `--execute`; S3 listing total after | Dry-run output, listing |
| 5. Manifests and checksums | `verify_all` over each `raw/<source>/` | 0 problems |
| 6. Pandera schemas | Offline tests with good and bad fixtures; run on the real data before load | `pytest` output |
| 7. Idempotent load | Load twice, compare table hashes | Hash comparison |
| 8. Recount | Count rows in the raw files independently and compare with the table | Recount script output |
| 9. Sources | Query: no loaded layer without a `data_sources` row | Query output |
| 10. No credentials committed | Search the diff and manifests for keys | Search output |
| Whole task | `make check`, then `/code-review` on the branch before the PR | Command output |

## Results (fill in after implementation)

- **Date completed:**
- **What was run:**
- **Passed:**
- **Failed or skipped:**
- **Evidence location:**
- **Roadmap exit check met:**
- **Roadmap tracker updated:**
