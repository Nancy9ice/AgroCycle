# Requirements

## Add your field
- The home page's primary button and the closing banner say "Add your field" and open `/field` on "My field". The demo is a secondary choice ("Try a demo field").
- `/field` shows two tabs: "My field" and "Demo fields". A link with `?field=` opens "Demo fields" so returning from the profile still works.
- Drawing: tap to add a corner; "Add corner at centre" adds one under the crosshair; Undo, Start again, Finish. At least three corners.
- A finished boundary shows area in acres and hectares, the county, and any problem in plain words. It is checked with `features/field/geometry.ts`.
- "Use my location" moves the map to the farmer and says if they are outside Story and Boone. It asks the browser for permission, handles refusal and no support, and never sends the position anywhere.
- A valid boundary does not get a profile or a comparison. The page says why and offers a demo field.

## Questions
- "Fill in a starting point" sets Medium for the five priorities and "Not sure" for each farm question that has a "Not sure" option. No yes or no is ever filled in. "Clear all answers" undoes it.

## Not connected
- When the web app has no data service configured, the compare page says so. When it does and an indicator is missing, today's note stays.

## Words and phone
- No screen a farmer meets uses a bare degree grid, "reanalysis", "NDVI", "HLS", "SSURGO", "CDL", "GDD", "applicability" or "provenance" without a plain-word explanation next to it.
- No sideways scroll at 360 px; controls at least 44 px tall.

## Asked of the team (not built here)
- BE: store a boundary and give it a status (`processing`, `ready`, `failed`); serve `/profile` and `/compare` for it.
- DE and DS: run crop history (CDL), soil (SSURGO), weather (NASA POWER) and greenness (HLS) for one new polygon on request, with the same quality flags.
