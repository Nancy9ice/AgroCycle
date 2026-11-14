# Requirements: Field profile screen (step 2)

## Covers

- **PRD requirements:** FR-02 (crop history shown year by year with product and resolution noted), FR-03 and FR-04 (display only, with sample data), FR-05 (soil with survey context kept), FR-06 (missing inputs shown), FR-12 (traceability), NFR-02, NFR-08.
- **Roadmap exit check satisfied:** partly. The exit check ("the profile screen renders real crop-history, soil and climate data end to end") is met for crop history and soil from committed data. Weather and greenness are sample values until the pipeline and API exist.

## Inputs

- `data/fields/field_selection_notes.csv`: `crops_2015_2025` (one letter per year: C corn, S soybean, G grass or pasture, A alfalfa, H other hay, O oats, L clover, X other), `soil_series`, `soil_map_unit`.
- A sample fixture for weather and greenness (clearly labelled).

## Outputs

- `/fields/[fieldId]/profile` for all 45 demo fields; unknown ids show the not-found page (the HTTP status is 200 because the page streams from behind a loading shell).
- `/fields/[fieldId]/priorities` placeholder.
- `FieldProfile` contract in `web/src/features/profile/types.ts`.

## Acceptance criteria

1. The page shows, for any of the 45 fields: availability strip, crop history (11 years, 2015 to 2025), weather, greenness, soil.
2. Crop history is the real sequence for that field. The summary sentence matches the sequence: alternating, repeated crop years named, single crop, or mixed. Unit tests cover each case and all 45 fields.
3. Soil shows the real series and map unit for that field, says it is read at the field centre point, and shows drainage, organic matter and texture as "not loaded yet", not as values.
4. Weather and greenness carry a visible "Sample values" label on the section, in the availability strip and in their drawers. No weather or greenness number appears without it.
5. Each greenness month shows its valid-image count. Months the data layer marks `unknown` are drawn as unknown, not as bare or growing, and the chart has a text alternative (table) for screen readers.
6. Every indicator and section has a "Where this comes from" control that opens the drawer with: what it is, source (with link), how precise it is, what is missing, technical record. The drawer closes with Esc, the close button and a click on the backdrop, and returns focus to the control that opened it.
7. Every card shows an evidence label (PRD §6.2). The Simple/Detailed toggle shows or hides the technical lines; the label stays.
8. Edge-case fields show the edge-case note. Unknown dimensions are labelled, never shown as neutral.
9. The page contains no yield, profit or outcome claims, and says NDVI-style greenness is not yield or soil health.
10. "Back to choosing a field" returns to `/field?field=<id>`; "Next: what matters to you" reaches the placeholder.
11. `npm run check` passes; no horizontal scroll at 360, 390, 768 and 1280 px; console is clean.

## Evidence labels, scale and limitations to preserve

- Crop history: classified output, 30 m cells (resampled 30 m for 2024 and 2025); agreement with another classification, not a farm record.
- Soil: survey information, mapped unit at the field centre point, not a soil test.
- Weather: model/reanalysis, grid of about 50 km, not a field measurement (sample values).
- Greenness: derived indicator, 30 m, cloud-screened, valid-image counts shown (sample values).

## Out of scope

Real weather and greenness data, the API call, Priorities, Compare and Plan screens, soil moisture and rainfall comparison layers, charts for climate time series, printing.
