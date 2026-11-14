# Requirements: Validation page

## Covers

- **PRD requirements:** PRD §11 (validation and testing, and its terminology rule), §16 (limitations disclosed, stakeholder gap acknowledged, claims evidenced), NFR-02, NFR-03, NFR-08.
- **Roadmap exit check satisfied:** none by itself; it presents Phase 14's evidence as it stands.

## Inputs

Static, typed content in `features/validation/content.ts`, each row sourced to a spec or the tracker.

## Outputs

`/validation`.

## Acceptance criteria

1. Nine rows, one per PRD §11 component, each with: what was checked, the result as recorded, what it does not show, the source document, and a status for each of the four evidence kinds (done, partly, not done).
2. The four kinds are explained in plain language and never merged; no row uses the word "validated" for an internal test.
3. A summary strip counts rows by kind (done and partly), derived from the rows; a test fails if any row lacks one of the four kinds.
4. The Marsden 2-year manufactured nitrogen mismatch is shown in its own callout with both numbers.
5. User review is shown as not done, with the acknowledgment of the gap; expert review is shown as not done for every row.
6. The page shows the snapshot date, says counts are as recorded in the specs, and says which results are from synthetic or sample data (indicator functions not run on real field values).
7. No score, no overall "accuracy" figure, no claim of readiness.
8. Reachable from the footer and from the comparison's limits section.
9. `npm run check` passes; no horizontal scroll at 360, 390, 768, 1280 px; console clean.

## Evidence labels, scale and limitations to preserve

Each statement keeps its source's own scope: one site, one pull, synthetic frames, not expert-reviewed.

## Out of scope

Live test results, CI badges, an interactive confusion matrix (Phase 14 will produce one), user feedback intake.
