# Validation: Adviser summary (step 5)

## Checks

| Requirement / criterion | How it will be verified | Evidence kept |
| --- | --- | --- |
| 1 Content | Read the page for a rotation field and a corn field | Notes below |
| 2 Wording, no score | Read copy; search for banned words | Notes below |
| 3 Adviser questions | `npm test`; count in browser | Test output, notes |
| 4 Preview banner / abstention reason | Open with and without `preview=sample` | Notes below |
| 5 Evidence list | Compare with the rule table | Notes below |
| 6 Print | Chrome print emulation, screenshot | Screenshot |
| 7 Links | Read hrefs | Notes below |
| 8 Check and layout | `npm run check`; widths; console | Command output |

## Results (fill in after implementation)

- **Date completed:** 2026-11-14 (implementation); manual checks listed below are still open
- **What was run:** `npm run check` (ESLint, `tsc --noEmit`, Prettier check, 157 unit tests, `next build`); a scripted Chrome session (DevTools protocol) against the production build: abstention, preview all-yes, a corn field, print media emulation, link hrefs, unknown id, 4 widths, console capture, screenshots.
- **Passed:**
  - 1: field, county, boundary source, crop history, outcome with engine reason, three options with reasons, all 12 questions (answered or "Not provided"), questions to ask, evidence list, limitations and rules version are present. A corn field shows abstention and "Not offered" options.
  - 2: wording is "brief" and "summary"; the page says it is not a prescription or a yield/profit prediction; no score or ranking.
  - 3: 5 unit tests; in the browser an abstention run gives 26 questions (4 farmer answers, rules, 6 data gaps, 7 unsourced claims, 3 standing), an all-answered preview run gives 11 (no farmer questions).
  - 4: `?preview=sample` shows the sample-values banner; without it the abstention reason is in the result block.
  - 5: five claimable outcomes with their evidence badge and source; four not-assessed outcomes listed as having no data.
  - 6: in print media the header, footer, step bar and the print button are hidden (`display: none`).
  - 7: "Back to the comparison" and "Change my answers" keep answers and the preview flag; the comparison links here with both.
  - 8: no horizontal overflow at 360, 390, 768, 1280 px; console empty; unknown id gives the 404 page.
- **Added later (2026-11-14):** limiting answers to the three constraints no rule reads (hay equipment "No" or "Not sure", storage "No" or "Not sure", extra help "Little") now appear in the brief as questions, each saying it did not change the result. 3 unit tests, including that the outcome is unchanged. Rules for these three remain DS2's decision (none sourced).
- **Failed or skipped:** an actual print or PDF was not inspected on paper; the 26-question list for an abstained result is long and may need trimming after adviser feedback; the boundary provenance string is DE's text unchanged and mentions an internal script path.
- **Evidence location:** scratchpad screenshots `plan-desktop.png`, `plan-mobile.png`; test output.
- **Roadmap exit check met:** with step 4, the core journey works end to end for the demo field; the API call and real indicators remain.
- **Roadmap tracker updated:** yes, 2026-11-14 (left "In progress")
