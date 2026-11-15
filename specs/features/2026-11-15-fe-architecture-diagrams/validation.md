# Validation: Architecture and lineage diagrams

## Results

- **Date completed:** 2026-11-15
- **What was run:** `python3 docs/diagrams/build.py`; both SVGs parsed as XML; PNGs rendered with headless Chrome at 2x and looked at; the first render had a clipped last box, overlapping "Not built" labels, a status label wider than its box, arrow labels colliding with box edges and a diagonal arrow through text; each was fixed and the figures re-rendered and looked at again.
- **Passed:** criteria 1 to 7 on the final renders.
- **Failed or skipped:**
  - Status is a snapshot of 2026-11-15 and will go stale.
  - The ClickHouse-reading API stage is amber because it has not run against the live database.
  - Thresholds in the lineage figure are typed in the generator, not read from the code; if DS2 changes a rule, the figure must be edited by hand.
- **Evidence location:** `docs/diagrams/`.
- **Roadmap tracker updated:** yes, 2026-11-15 (row added, left "In progress")
