# Validation: Priorities and constraints form (step 3)

## Checks

| Requirement / criterion                 | How it will be verified                                         | Evidence kept      |
| --------------------------------------- | --------------------------------------------------------------- | ------------------ |
| 1 12 optional questions                 | Count fieldsets in the browser; submit with none answered       | Notes below        |
| 2 Why-we-ask and tags                   | Read each question; count the "Used in the comparison" tags (4) | Notes below        |
| 3 Engine mapping                        | `npm test`                                                      | Test output        |
| 4 URL codec                             | `npm test`; open a hand-edited URL in the browser               | Test output, notes |
| 5 Answer, change, clear; keyboard       | Scripted browser run and arrow keys                             | Notes below        |
| 6 Summary wording and count             | Read the panel at 0, some and 12 answers                        | Notes below        |
| 7 Answers reach the compare placeholder | Click "Compare strategies"                                      | Notes below        |
| 8 No outcome claims or score            | Read the copy                                                   | Notes below        |
| 9 Check and layout                      | `npm run check`; 360, 390, 768, 1280 px; console                | Command output     |

## Results (fill in after implementation)

- **Date completed:** 2026-11-14 (implementation); manual checks listed below are still open
- **What was run:** `npm run check` (ESLint, `tsc --noEmit`, Prettier check, 136 unit tests, `next build`); a scripted Chrome session (DevTools protocol) against the production build that answered, changed, cleared and keyboard-changed questions, followed "Compare strategies" and "Change my answers", opened a hand-edited URL, measured width at 360, 390, 768 and 1280 px, and captured console output and screenshots.
- **Passed:**
  - 1: 12 fieldsets (5 priorities, 7 constraints); none is required; a fresh page has 0 answers and the "Compare strategies" link works.
  - 2: every constraint carries a reason; 4 are tagged "Used in the comparison" and 3 "Recorded for your adviser"; the 5 priorities are tagged "Changes what we highlight".
  - 3: unit tests cover the four context keys, every option of the four engine questions, and that priorities and recorded-only constraints change nothing. "Not sure" and unanswered both give `null`, never `true`.
  - 4: tests cover round trip, omitted answers, unknown keys and values, and a repeated key. In the browser `?soil=extreme&manure=yes&x=1` restored only "Yes" for manure.
  - 5: answering writes the URL (`?soil=high&manure=no`), ArrowRight moves the radio from "No" to "Not sure" (`manure=unsure`), "Clear answer" removes it and the count drops.
  - 6: the summary says "Answered so far: N of 12" and that unanswered questions are never treated as "yes"; the count updated 0, 1, 2.
  - 7: "Compare strategies" carries the answers; the compare placeholder lists all 12 questions with the answer or "Not provided"; "Change my answers" returns to the form with every answer restored.
  - 8: no yield, profit or outcome claims and no score; the page says profit is not guessed.
  - 9: no horizontal overflow at 360, 390, 768 and 1280 px; console empty on the production build.
- **Failed or skipped:**
  - Not tested with a screen reader, and tabbing through all twelve questions was not tried by hand. Radios are native, so arrow keys work as the browser provides.
  - The phone layout was measured, not looked at in a screenshot of the finished state.
  - Bugs found and fixed during testing: answers clicked in quick succession were lost, because each click rebuilt them from a URL that had not updated yet (answers are now held in state and mirrored into the URL); "Change my answers" on the compare page dropped the answers (the link now carries them).
  - Wording for farmers has not been reviewed by the farmer reviewer.
- **Evidence location:** commands run in the session; screenshots were kept in the session scratchpad, not committed.
- **Roadmap exit check met:** not for Phase 11 as a whole (needs the comparison UI).
- **Roadmap tracker updated:** 2026-11-14, left `In progress` until the farmer review and the comparison UI.
