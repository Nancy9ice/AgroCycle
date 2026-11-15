# Validation: Validate and load the Marsden records

## Checks

| Criterion | How it is verified | Evidence |
|---|---|---|
| 1. Outputs validate | Offline: his schemas and the DE's on synthetic frames, including a unit error, a wrong sum and an unknown rotation. Live: his real outputs | pytest output |
| 2. PRD targets | Offline: the 12 exact targets as golden values on a frame built from his numbers. Live: rerun his script and read the loaded summary rows | pytest output, query |
| 3. The gap stays visible | Offline and live: the UNRECONCILED and INFO rows load with their notes; a test fails if the status is changed | pytest output |
| 4. Lossless conversion | Offline: every cell of both wide frames appears once in the long frame; `applied = manufactured + manure` | pytest output |
| 5. Lineage link | Offline: an indicator without a lineage row is refused; the mapped rows validate against the lineage schema. Live: DS2's 21 rows have the same hash before and after | pytest output, hashes |
| 6. Input checksums | Live (skips without S3): the five SHA-256 values equal the S3 manifests | output |
| 7. Idempotent, portable | Live: load twice, compare hashes; `make check` with raw files and S3 absent | hash values, output |
| Hand-check | DS2 is told the lineage mapping and the run id convention; his reproduction is not changed | message |

Merge when: every row is green, the code review findings are fixed, and the tracker row is updated.

## Results (fill in after implementation)

- **Date completed:**
- **What was run:**
- **Passed:**
- **Failed or skipped:**
- **Evidence location:**
- **Roadmap exit check met:**
- **Roadmap tracker updated:**
