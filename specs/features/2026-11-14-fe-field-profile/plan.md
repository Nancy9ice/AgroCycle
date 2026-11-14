# Plan: Field profile screen (step 2)

- **Role:** fe
- **Spec created:** 2026-11-14
- **Roadmap phase and task:** Phase 7, FE: profile and evidence drawer (second screen of the core journey, PRD §5.2 steps 2 to 4)

## Goal

Show what is known about the selected field: what was grown each year, the soil, the weather, and how green the field is through the year. Every number says what kind of evidence it is, how coarse it is, and where it came from.

## Approach

- **The contract comes first.** There is no OpenAPI draft yet, so `web/src/features/profile/types.ts` defines the profile shape (`FieldProfile`) in the spirit of `GET /fields/{id}/profile` from `specs/tech-stack.md`. Each section carries a `status` (`available`, `sample` or `not_loaded`), its data and its provenance. When BE publishes the real schema, only the data layer changes.
- **Real data where it exists, labelled sample where it does not.**
  - Crop history (2015 to 2025) and soil series come from DE's committed `field_selection_notes.csv` (CDL and SSURGO at the field), copied by `npm run sync:data`. Status `available`.
  - Weather (POWER-style indicators) and satellite greenness (HLS-style monthly series) are not in the repo yet. They come from one clearly marked sample fixture, shown with a visible "Sample values" label on the section and in the provenance drawer. Status `sample`. The same values appear for every field, which is the reason for the label.
  - Soil moisture from space is shown as "Not checked".
- **No decision logic in the UI.** States such as "bare" or "unknown" and the plain-language summaries are produced in the data layer (the stand-in for the API). The components only render them.
- **Provenance drawer.** One reusable drawer (native `<dialog>`) answers "where does this number come from": what it is, source, how precise, what is missing, and the technical record (evidence type, scale, variable, version, indicator id), covering FR-12.
- **Simple and Detailed view.** A toggle reveals technical lines on each card. The evidence label is always visible.
- **Edge-case fields** (not a maize–soybean rotation) show the same note as on the field screen.
- Routes: `/fields/[fieldId]/profile` (this screen). "Next: what matters to you" goes to a placeholder `/fields/[fieldId]/priorities`.

## Files, tables and endpoints

- `web/src/features/profile/` (contract, data layer, sections, drawer, tests), `web/src/domain/crops.ts`.
- `web/scripts/sync-field-data.mjs`: also writes `profile-source.generated.json`.
- `web/src/app/fields/[fieldId]/profile/page.tsx` (replaces the placeholder), `.../priorities/page.tsx` (placeholder).
- `web/src/app/globals.css`: crop colour tokens for grass, hay, clover and other.
- No tables or endpoints.

## Steps (in order)

1. Spec, contract types, crop vocabulary.
2. Sync script extension; crop-history builder with tests.
3. Data layer (`getFieldProfile`) and the sample fixture.
4. Drawer, view toggle, indicator card, section components.
5. Compose the page; placeholder for step 3.
6. `npm run check`, browser check at desktop and phone widths.

## Dependencies and interfaces with other roles

- **BE:** the contract in `types.ts` is a proposal. Please compare it with the OpenAPI draft; the names `evidence_type`, `scale` and `indicator_id` follow `specs/tech-stack.md`.
- **DS1/DS2:** the sample greenness and weather values are placeholders, not results. "Bare" and "unknown" states and any thresholds must come from DS1's rules through the API.
- **DE:** reads `crops_2015_2025`, `soil_series`, `soil_map_unit` from the notes CSV.

## Risks and open questions

- Sample sections could be mistaken for real results. Mitigation: a labelled banner on each, the "Sample values" status in the availability strip, and in the drawer. They must be removed or replaced before any claim is made from the demo.
- 2024 and 2025 crop history use the resampled 30 m CDL (DE's finding). The drawer says so.
- Crop sequences exist only for 2015 to 2025, not 2008 to 2025 as in the early design.
