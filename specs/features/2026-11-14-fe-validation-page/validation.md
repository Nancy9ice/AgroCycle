# Validation: Validation page

## Checks

| Requirement / criterion | How it will be verified | Evidence kept |
| --- | --- | --- |
| 1 Nine rows, complete | `npm test`; count in browser | Test output, notes |
| 2 Kinds never merged | Read the copy | Notes below |
| 3 Derived summary | `npm test` | Test output |
| 4 Marsden callout | Read the page | Notes below |
| 5 User and expert review not done | Read the page | Notes below |
| 6 Snapshot date and caveats | Read the page | Notes below |
| 7 No score or readiness claim | Read the copy | Notes below |
| 8 Links | Follow the footer and comparison links | Notes below |
| 9 Check and layout | `npm run check`; widths; console | Command output |

## Results (fill in after implementation)

- **Date completed:** 2026-11-14 (implementation); manual checks listed below are still open
- **What was run:** `npm run check` (ESLint, `tsc --noEmit`, Prettier check, 164 unit tests, `next build`); a scripted Chrome session against the production build: row and chip counts, summary counts, callout, footer and comparison links, 4 widths, console capture, screenshot.
- **Passed:**
  - 1: nine rows, each with four kind chips; tests require nine unique components and all four kinds on every row.
  - 2: the four kinds are explained in plain language and shown separately; a test fails if an internal-test row says "validated".
  - 3: summary derived from the rows: own tests 6 of 9 done and 2 partly; another source 0 done and 2 partly; independent reference 0; expert review 0. A test fixes independent and expert at zero because none is recorded.
  - 4: the Marsden callout shows 80 and 74.5 and says the check stays failing.
  - 5: user review is "not done" with the gap stated; expert review is "not done" on every row.
  - 6: the snapshot date is on the page, with "as recorded there, not re-run"; the weather, soil and synthetic-data caveats are on the rows.
  - 7: no score, no overall accuracy, no readiness claim.
  - 8: the footer and the comparison's limits section link to `/validation`.
  - 9: no overflow at 360, 390, 768, 1280 px; console empty.
- **Failed or skipped:** the content is a hand-maintained snapshot and will go stale; the test counts come from each spec's recorded results and were not re-run for this page; nobody from DS1, DS2 or DE has reviewed the wording of their rows.
- **Evidence location:** scratchpad screenshot `val-desktop.png`; test output.
- **Roadmap exit check met:** n/a (presents Phase 14 evidence as it stands).
- **Roadmap tracker updated:** yes, 2026-11-14 (left "In progress")
