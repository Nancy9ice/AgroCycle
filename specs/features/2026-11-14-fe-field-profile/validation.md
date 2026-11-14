# Validation: Field profile screen (step 2)

## Checks

| Requirement / criterion         | How it will be verified                                                     | Evidence kept  |
| ------------------------------- | --------------------------------------------------------------------------- | -------------- |
| 1 Sections for every field      | Load all 45 profile pages in a script and check each section heading exists | Script output  |
| 2 Crop summary matches sequence | `npm test` (cases and all 45 fields)                                        | Test output    |
| 3 Soil values and "not loaded"  | Compare with the CSV for several fields; read the page                      | Notes below    |
| 4 Sample labelling              | Read each sample section, strip and drawer                                  | Notes below    |
| 5 Greenness states and table    | Inspect a month marked unknown; read the table                              | Notes below    |
| 6 Drawer behaviour              | Open from a card, close with Esc, backdrop and button; check focus          | Notes below    |
| 7 Evidence label and toggle     | Toggle Simple and Detailed                                                  | Notes below    |
| 8 Edge-case note                | Open `test-036`'s profile                                                   | Notes below    |
| 9 No outcome claims             | Read the copy                                                               | Notes below    |
| 10 Navigation                   | Click both buttons                                                          | Notes below    |
| 11 Check and layout             | `npm run check`; 360, 390, 768, 1280 px; console                            | Command output |

## Results (fill in after implementation)

- **Date completed:** 2026-11-14 (implementation); manual checks listed below are still open
- **What was run:** `npm run check` (ESLint, `tsc --noEmit`, Prettier check, 111 unit tests, `next build`); a script that fetched all 45 profile pages and checked each section heading and the "Sample values" label; a scripted Chrome session (DevTools protocol) against the production build that opened the drawer, closed it three ways, toggled Simple/Detailed, followed both navigation buttons, measured width at 360, 390 and 768 px, and captured console output and screenshots.
- **Passed:**
  - 1: all 45 profile pages contain the crop history, weather, greenness and soil sections.
  - 2: the crop summary tests pass (alternating, one and several repeated years, single crop, mix, corn-heavy not called alternating) and every one of the 45 fields builds 11 years from 2015 to 2025 whose crops agree with its class.
  - 3: the soil series and map unit shown are the field's own values from the data files; drainage, organic matter and texture appear as "not loaded yet".
  - 4: the weather and greenness sections, the availability strip and their drawers all say "Sample values".
  - 5: months with too few clear images carry no value and are drawn as a dashed "?" box; each month shows its clear-image count; a hidden table gives screen readers the same data.
  - 6: the drawer opens from a card, closes with Esc, a click on the backdrop and the close button; focus returns to the opening button; the page behind it does not scroll while it is open.
  - 7: every card shows an evidence label; Detailed adds four technical lines (one per weather card).
  - 8: `test-036` shows the edge-case note and its own crop and soil values.
  - 9: no yield, profit or outcome wording; the greenness section says greenness is not yield or a soil measurement.
  - 10: "Back to choosing a field" returns to `/field?field=test-036`; "Next: what matters to you" reaches the placeholder.
  - 11: `npm run check` passes; no horizontal overflow at 360, 390 and 768 px (390 px measured on a mobile viewport); console empty on the production build.
- **Failed or skipped:**
  - Keyboard use beyond Esc and focus return was not tested by hand (tab order through the cards and toggle).
  - Not tested with a screen reader.
  - Unknown ids show the not-found page but return HTTP 200 (streaming).
  - Bugs found and fixed during testing: a corn-heavy sequence was described as "mostly alternating" (caught by a unit test); the hidden table made the phone page 583 px wide because browsers do not clip a `sr-only` table (wrapped in a clipped div); month columns were too tight on phones (single-letter month labels below 640 px).
  - The dev server on port 3004 served a stale stylesheet that lacked the scroll-lock rule; the production build has it. Restarting `npm run dev` clears this.
- **Evidence location:** commands run in the session; screenshots were kept in the session scratchpad, not committed.
- **Roadmap exit check met:** partly. Crop history and soil are real; weather and greenness are labelled sample values until the pipeline and API exist.
- **Roadmap tracker updated:** 2026-11-14, left `In progress` until the sample sections are replaced with real data.
