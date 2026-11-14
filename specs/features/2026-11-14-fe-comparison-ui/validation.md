# Validation: Comparison UI (step 4)

## Checks

| Requirement / criterion | How it will be verified | Evidence kept |
| --- | --- | --- |
| 1 One outcome, no score | Read all copy; search the DOM for rank/score/best/winner | Notes below |
| 2 Abstention default | Open a rotation field with no preview | Screenshot, notes |
| 3 Preview reaches all outcomes | Scripted runs with all-yes, some unknown, no manure, no forage outlet | Notes below |
| 4 Three strategies | Count strategy cards; read feasibility reasons | Notes below |
| 5 Nine outcomes, unknown never blank | Count cards and statuses; read withheld ones | Notes below |
| 6 Marsden figures | Unit test ties figures to DS2 text; read the cards | Test output |
| 7 Priorities highlight only | Set priorities; outcome unchanged | Notes below |
| 8 Questions | Unanswered answers listed; link keeps answers | Notes below |
| 9 Limitations visible | Read the page | Notes below |
| 10 Parity with Python engine | `npm test` (parity test) after `npm run sync:engine` | Test output |
| 11 Out-of-domain fields | Open a corn, pasture and mixed field | Notes below |
| 12 Check and layout | `npm run check`; 360/390/768/1280 px; console | Command output |

## Results (fill in after implementation)

- **Date completed:** 2026-11-14 (implementation); manual checks listed below are still open
- **What was run:** `npm run check` (ESLint, `tsc --noEmit`, Prettier check, 152 unit tests, `next build`); `npm run sync:engine` against the real `engine/decision.py`; a scripted Chrome session (DevTools protocol) against the production build over 9 scenarios, 4 widths, console capture and screenshots.
- **Passed:**
  - 1: one outcome only; copy has no score, rank or winner (the words "recommendation", "rank", "best" appear only in negations such as "This is not a recommendation").
  - 2: default for a rotation field is abstention ("We cannot compare these options for this field yet"), listing the unstated answers and unknown indicators; all 3 strategies and all 9 outcomes still shown (5 "Held back", 4 "Not assessed").
  - 3: with `?preview=sample` a notice states the values are sample; all yes gives "Worth exploring further"; no answers gives "A comparison, with caveats"; no manure makes applied nitrogen "Does not carry over" and leaves herbicide "applies"; no hay outlet makes option C "Not available for you" and B stays.
  - 4: three strategy cards with ribbon, feasibility in words with a glyph, engine reasons, operational requirements.
  - 5: nine outcome cards each with a status, caution always shown; withheld and not-assessed never blank.
  - 6: `marsden-figures.test.ts` ties each number to DS2's statement; figures render per option with units and "one Iowa research site, nine years".
  - 7: priorities tag outcomes and say soil and dry/wet years cannot be spoken to; unit test shows priorities do not change outcome or statuses.
  - 8: open questions split into "only you" and "field data"; the link keeps answers.
  - 9: limitations, unsourced crop ideas, rules version and "not expert-reviewed" are on the page.
  - 10: `engine-parity.test.ts`: the TypeScript port equals the Python engine for 567 cases (7 profiles x 81 combinations) and reaches all three outcomes.
  - 11: continuous corn and pasture fields abstain with all outcomes "Does not carry over" and options "Not offered for this field"; an unknown id gives the 404 page.
  - 12: no horizontal overflow at 360, 390, 768, 1280 px (a figures table overflowed at 360 px and was rebuilt as a grid); console empty.
- **Failed or skipped:** keyboard tabbing and screen-reader pass not done; farmer wording review not done. Some of DS2's `caution` strings contain internal jargon ("PRD 7.4", "research_needed") and are shown unchanged, since the UI must not rewrite engine evidence text; DS2 should provide plain-language versions.
- **Evidence location:** scratchpad screenshots `cmp-default-desktop.png`, `cmp-explore-desktop.png`, `cmp-mobile.png`; test output.
- **Roadmap exit check met:** partly. Field, profile, priorities and compare work for the demo field; the plan step, real indicators and the API call are open.
- **Roadmap tracker updated:** yes, 2026-11-14 (left "In progress")
