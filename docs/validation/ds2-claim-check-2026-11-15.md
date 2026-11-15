# AgroCycle claim check — PRD §16 Definition of Done

**Date:** 15 November 2026 · **Author:** DS2 · **Rules version:** `2026-11-15.2`

Each item of the Definition of Done, what supports it, and an honest verdict. **Met** means the evidence is in
the repository or the database and can be checked. **Partly met** means something real supports it but a named
piece is missing. **Not met** means we cannot claim it today.

The purpose is to find the claims we cannot support before a judge does. Companion to
`ds2-validation-summary-2026-11-15.md`.

| # | Item | Verdict | Evidence, or what is missing |
|---|---|---|---|
| 1 | Problem and intended user defined and supported by evidence | **Met** | PRD §2.1–2.2; the decision question is anchored to a real maize–soybean starting point. |
| 2 | Field geometry identified and provenance recorded | **Met** | `fields` (45 rows) and `data/fields/fields.geojson` carry `boundary_source` and a `provenance` string per field. Every one is `demo` — team-drawn, not a real farm boundary — and is labelled so. |
| 3 | NASA data plays a meaningful, demonstrable role | **Met** | NASA POWER: 626,416 daily rows driving 9 climate indicators across 45 fields. NASA HLS: 9,663 NDVI rows and 127 bare-field windows. Both are inputs to the comparison, not decoration. |
| 4 | At least three rotation strategies including the existing one compared | **Met** | A (two-year), B (three-year oat/red clover), C (four-year oat/alfalfa) in the rule table; all three returned on every assessment, including when one is unavailable. |
| 5 | Comparison covers relevant dimensions, unsupported ones marked unknown | **Met** | 9 outcomes, of which 3 are `claimable=False` and always return "not assessed". 20 indicator rows are `partial` and say over what. A test asserts the forbidden outcomes cannot be claimed. |
| 6 | Data sources, versions and processing methods documented | **Met** | `indicator_lineage` (25 rows, no indicator without one), `data_sources` (10), per-file SHA-256 manifests, `docs/sources/`, `docs/method/ds2-scientific-method.md`. |
| 7 | **Crop-history outputs evaluated with the correct validation terminology** | **Not met** | `scripts/cdl_confusion_matrix.py` compares CDL with itself across years — internal consistency, not agreement with another classification — and has not been run (`data/out/phase3/` absent). The classification decides which 18 fields the engine declines for, so this is load-bearing. **Owner: DS1.** |
| 8 | Marsden calculations reproducible from retrieved source records | **Met** | 44 tests; `marsden_reconciliation` 17 MATCH, 1 WITHIN_SEM, 1 UNRECONCILED (documented 2011 gap), 1 INFO. Loaded figures match the PRD targets exactly. Inputs verified against SHA-256 manifests before every run. |
| 9 | Scientific limitations and evidence types disclosed | **Met** | Every indicator carries `evidence_type` and a `limitation`; every outcome carries a `caution` and a source line; the summary's §5 lists what is not validated. |
| 10 | Transferability assessed rather than assumed | **Partly met** | Applicability is assessed per outcome, so no manure removes the nitrogen comparison and leaves herbicide intact. But 9 of 14 rules never fire on this test set, two were withdrawn as unsourced, and none is expert-reviewed. The mechanism is real; the assessment is thin, and the summary says so. |
| 11 | Farmer operational and market constraints represented | **Met** | Four constraints reach the engine (manure, forage outlet, oat outlet, small-grain equipment) and change the outcome: all 27 in-domain fields move from "worth exploring" to "qualified comparison" when manure is unstated. Three further constraints are collected by the form and read by nothing — see action 4. |
| 12 | The decision engine can qualify its output or abstain | **Met** | Demonstrated on real data, not asserted: 18 abstentions and 27 qualified comparisons in `engine_test_set`, plus 37 unit tests over in-domain, out-of-domain, missing-data and abstention cases. |
| 13 | The end-to-end product works | **Not verified by me** | `/fields/{id}/compare` exists and calls `engine.assess`; the web app has field selection, profile, priorities and comparison pages; ClickHouse holds the data. I have not run the stack end to end. **Owner: BE and FE**, before the demo. |
| 14 | Stakeholder engagement documented, or the gap acknowledged | **Met by acknowledgement only** | There has been no engagement with an Iowa farmer or adviser. The gap is stated in the summary §5 and must be stated on the slide too. The farmer reviewer is Nigerian; his feedback will cover usability and general agronomic sense and must be labelled that way. **No adoption or local-impact claim is supportable.** |
| 15 | Slides show actual functionality, real screenshots | **Not met** | No deck exists yet. **Owner: whole team.** |
| 16 | Every competition claim supported by evidence | **Open** | Cannot be closed until the deck exists. The wording actions below are the known risks. |

---

## Wording that must change before the deck

These are the claims most likely to be made carelessly, and what the evidence actually supports.

1. **Never "total nitrogen".** Say **applied nitrogen (manufactured plus manure)**. It excludes biological
   fixation, which the paper reports as substantial, and most of the diversified systems' nitrogen came from
   manure. "78–85 % less nitrogen" is wrong; "manufactured nitrogen was 78–85 % lower, with manure supplying
   much of the rest" is right.

2. **Never "we validated the crop history".** Nothing has been validated against an independent reference.
   Say what was done: documented, versioned classification rules applied to CDL.

3. **Never "less herbicide means less harm".** The figure is mass of active ingredient. It says nothing about
   toxicity or exposure, and excludes insecticides applied in 2007–2009.

4. **Never "the app shows soil-health improvement".** Soil carbon, erosion and nitrate leaching are not
   claimable and return "not assessed". Nothing we have measures them on a field.

5. **Never "proven on 45 Iowa fields".** They are 45 team-drawn demonstration polygons in two counties,
   cleaner than real boundaries, with the in-domain split chosen rather than sampled. Results are indicative,
   not statistically strong.

6. **Never "farmer-validated" or "ready for adoption".** See item 14.

7. **On the AI assistant, say what it does.** The `/ask` endpoints use an LLM, constrained by prompt to answer
   only from the stored analysis and lineage, to cite indicator ids, to refuse out-of-scope questions and
   never to rank strategies. That matches the PRD's rule that AI may phrase already-computed outputs and must
   not generate evidence. Two honest caveats: the constraint is a prompt, not a guarantee the way the
   deterministic engine is testable, and the right claim is **"AI phrases results the engine computed"**, not
   "no AI" and not "AI analyses your field".

## Actions, with owners

| # | Action | Owner |
|---|---|---|
| 1 | Run a CDL check against an independent reference, or state plainly on the slide that the classification is rule-based and unvalidated | DS1 |
| 2 | Run the stack end to end and capture real screenshots | BE, FE |
| 3 | Farmer walk-through and feedback log, labelled as usability and general agronomy only | F, DS2 |
| 4 | Decide whether `hayEquipment`, `storage` and `labour` are context-only, or need rules | DS2, FE |
| 5 | Apply the wording list above to every slide and to the README | whole team |
| 6 | Either get an agronomist to review the rule thresholds, or label them unreviewed wherever they are shown | DS2 |

## What I would say if asked "what is weakest?"

The crop-history classification. Everything downstream — which fields the engine answers for, the 18
abstentions, the whole in-domain story — rests on classification rules that have been self-reviewed and never
checked against anything external. It is the one gap that could change a result rather than only a caveat.
