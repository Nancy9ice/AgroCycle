# Validation: Accessibility and keyboard pass

## Checks

| Requirement / criterion | How it will be verified | Evidence kept |
| --- | --- | --- |
| 1 Axe | Scripted run on 10 page states | Notes below |
| 2 Names and focus ring | Scripted Tab walk | Notes below |
| 3 Skip link | Tab once, press Enter | Notes below |
| 4 Radio groups | Arrow keys and Tab | Notes below |
| 5 Drawer | Keyboard open, Tab, Escape | Notes below |
| 6 Map | Tab through; list alternative | Notes below |
| 7 Check | `npm run check` | Command output |
| 8 Honest scope | Read the results | This file |

## Results (fill in after implementation)

- **Date completed:** 2026-11-15 (keyboard walk only; the automated scan was not run)
- **What was run:** a scripted keyboard walk in headless Chrome against the production build: Tab pressed through home, field (map), profile, priorities, compare, brief and validation; the skip link; the provenance drawer; a radio group. For every stop the script recorded the element, its accessible name, whether a focus indicator was visible and whether it was on screen.
- **Passed:**
  - 1 (automated scan): **not run.** The first attempt, which loaded a downloaded copy of axe-core into the browser, was blocked by the permission system and was not retried by another route. No WCAG scan has been done.
  - 2: across the seven pages (about 20 to 50 stops each) **no focusable control lacked an accessible name, none lacked a visible focus indicator, and none was off screen.**
  - 3: the skip link is the first stop on every page; pressing Enter moves the next Tab to the first control inside `main`.
  - 4: the 12 radio groups on the priorities form give exactly 12 Tab stops (one per group); ArrowRight changes the answer ("Low" to "Medium"); Tab then leaves the group for that question's "Clear answer" button.
  - 5: the provenance drawer opens with Enter, focus moves inside, 12 further Tabs cycle only between the drawer's own controls and the browser's UI (never the page behind it), Escape closes it, and focus returns to the button that opened it.
  - 6: the map is not a keyboard trap: Tab passes through it and reaches the footer link; the field list offers every field.
  - 7: `npm run check` passes (no code changed).
- **Failed or skipped:**
  - **No automated WCAG scan** (see above). Colour contrast, heading order, landmark use and ARIA correctness were not machine-checked.
  - **No real screen reader** (VoiceOver, NVDA) was used. Reading order, whether labels make sense out of context, and whether the comparison is understandable by ear are unknown.
  - The walk checks that a focus indicator exists, not that it has enough contrast.
  - Only Chrome, only at 1280 px; no switch-device, voice-control or zoom testing.
  - Two reported "same control twice in a row" warnings and one count of 24 radio stops were the script's own artefacts (different groups with the same label "Low"; the walk wrapping to the top of the page), checked by reading the stop list.
  - No claim of WCAG conformance is made anywhere.
- **Evidence location:** the walk script was a scratchpad file and is not committed; results are recorded here.
- **Roadmap exit check met:** partly (keyboard operation verified; screen-reader and automated checks open).
- **Roadmap tracker updated:** yes, 2026-11-15 (row added, left "In progress")
