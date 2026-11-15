# Requirements: Make the screens and claims match real data

## Acceptance criteria

1. When the engine's `unknowns` contain no indicator, the comparison page shows no "why is every field not enough evidence" note and no sample-values offer. When it lists indicators, it shows them (the note says which kind of measurement is missing, not that all fields are the same).
2. The sample preview banner still shows whenever `preview` is true, whatever else is on the page.
3. No sentence on the validation page or in the README says that every real result is "not enough evidence", or that no indicator values exist; each statement is true with the API on and with it off.
4. The validation page states the live observation (26 of 27 in-domain fields reach "worth exploring" with every answer yes; 18 of 18 out-of-domain abstain; `test-022` withheld at 96.7 % organic-matter coverage), says it is an engine run on demonstration fields and not a validation, and keeps "no rule expert-reviewed".
5. The weather indicators row says the indicators exist for all 45 fields (4,390 of 4,410 rows complete) and still says they are not independently validated and POWER is a 50 km model.
6. The screenshot pack is re-taken against the API on live data; the guide's status for each shot is accurate (real weather and a real comparison result), with the constraint answers used written down.
7. The architecture diagram shows the API stage as built and the guide says why.
8. `npm run check` passes; no secret appears in any committed file or output.

## Out of scope

The crop-code vocabulary decision, the DS2 partial-season decision, a read-only database user.
