# Requirements: Architecture and lineage diagrams

## Covers

`PRD.md` §13 slide 4 and §12.1 ("a traceable path from NASA observations to an indicator, and how that indicator affects the decision"); §16 (limitations disclosed, claims evidenced).

## Acceptance criteria

1. The architecture figure shows source, ingest, S3, transform, ClickHouse, API and web app in order, each arrow labelled, and marks every box built, partly built, not built or external.
2. Things that are not built (HLS greenness features, Marsden tables in ClickHouse, evidence/lineage/upload endpoints) are drawn as dashed boxes, not omitted.
3. The lineage figure traces one indicator from the NASA variable to the outcome on screen, naming the evidence type of each step, the thresholds used, and all three effects the rules can have (caveat, caveat for unknown, withhold) plus "no effect".
4. The lineage figure states its own weakest points (the 300 degree-day band has no published basis; POWER is a model on a 50 km grid; no yield or profit claim).
5. Status matches `specs/roadmap.md` as of the date on the README; numbers match the rule table and the indicator code.
6. SVGs are valid, self-contained (no script, no external image), and carry a title and an accessible label; PNGs are rendered from them.
7. No text is clipped or overlapping in the PNGs.

## Out of scope

The deck, the scientific-method one-pager, per-indicator lineage for all 21 indicators.
