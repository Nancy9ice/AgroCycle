# Requirements: evidence hierarchy, adviser brief and engine authority

## Covers
- **PRD requirements:** §6.2 (evidence-type labels), §8.2 (unsupported dimensions are labelled, not neutral), §8.4 (required decision output), §8.5 (missing data is not favourable). Reviewer items 5.2, 5.3, 6.1.
- **Roadmap exit check satisfied:** Phase 11 (comparison UI shows evidence type and limits for every output).

## Acceptance criteria
1. The compare screen shows six evidence layers in the open (no drawer), each with a scope tag saying whose land it is about, and an explicit sentence that benefit figures come from research, not from the field's own measurements.
2. Every outcome appears in exactly one layer; the Marsden figures are under "Marsden experiment", the paper's findings under "published, not reproduced", unassessed outcomes under "assumed or unknown".
3. Each outcome card names its layer above the figure.
4. In the sample preview, substituted inputs are marked "sample value", never "used".
5. Unknown inputs are listed as not available; an empty layer says so.
6. The brief contains: field id, county, area, demonstration-polygon status; crop-history period and source; the ledger; each strategy's summary and requirements; priorities and constraints (marking the ones the rules read); withheld and unassessed outcomes with reasons; questions for local expert review; engine source, rules version, data version and data sources. It states it is not a prescription or a farm-management plan.
7. `getComparison` returns `provenance.source` `api` when the API answered and `offline_fallback` otherwise; with an API configured it never uses the local engine, even when the API fails.
8. The offline fallback is labelled on the compare screen and in the brief. In production without an API it throws unless `AGROCYCLE_ALLOW_OFFLINE_ENGINE=true`.
9. `api/tests/test_web_export_is_current.py` fails if the committed rule table or parity fixture differs from the engine in any way.

## Evidence labels, scale and limitations to preserve
The ledger adds no number and no claim. Marsden figures stay "experimental", the paper's findings stay "published"; scale stays "one research farm, nine seasons".

## Out of scope
Fetching Marsden figures from an API endpoint; expert review of the rules; a second brief format.
