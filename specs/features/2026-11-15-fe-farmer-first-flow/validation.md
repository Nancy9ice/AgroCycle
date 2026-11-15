# Validation

Run on 2026-11-15 against a production build of the web app and the API (file data source), in headless Chrome with touch emulation. Not a real device, and the sandbox could not download satellite pictures, so the map showed no imagery; drawing, location and layout were exercised, the look of the pictures was not.

## What was checked

| Check | Result |
|---|---|
| `tsc`, ESLint (0 errors), Prettier, Vitest | 217 tests pass (was 196): new tests for the drawing checks, the starting point, and the plain-words layer |
| Draw a field by real touch taps (3 taps, then "Add corner at the cross", then "Check my boundary") | 4 corners, "Your boundary looks good", 1.2 acres in Story County, honest "we cannot compare your own field yet" |
| Undo is locked once finished; "Change the corners" and "Start again" work | Yes |
| "Use my location" with a faked position inside Story County | Map moves, "You are in Story County" |
| Same, with a position in Des Moines | "You are outside Story and Boone counties" and a way to the demo |
| Position permission refused, or no support | Message with what to do next (unit-tested wording; the refused case was not driven in the browser) |
| `/field` tabs; `?field=` link from the profile still opens the demo tab | Yes |
| "Fill in a starting point" | Medium for the 5 priorities; "Not sure" for the 6 farm questions that offer it; extra help left blank; no yes or no filled in; editable; "Clear all answers" empties it |
| Site without a data service | Compare page says "not connected to the data", not "not enough evidence" |
| Sideways scroll on 8 screens at 360 and 390 px | None |
| Tap targets under 44 px | Raised to 44 px (logo, map buttons, toggles, footer and inline links, AI questions). One remaining: none found over 24 px after the last pass; rerun the audit after any layout change |

## Found by testing, fixed

- The map container collapsed to a 300 px strip, because MapLibre's stylesheet overrides a utility `absolute` class. Taps outside the strip never reached the map, so drawing silently failed. Fixed with an inline style.
- "Add corner at the cross" depended on the map's `load` event, which waits for every satellite picture. Now ready on style load, so a slow connection does not block it.

## Not done

- No real phone, no screen reader, no automated WCAG scan.
- Boundary file upload is still shown as not available.
- The refused-permission path was not driven in the browser.
- A drawn boundary is validated in the browser only. The API's `POST /fields` was not called; it does not store anything.
