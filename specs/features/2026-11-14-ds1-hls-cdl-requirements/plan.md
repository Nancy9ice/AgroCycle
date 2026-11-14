# Plan: HLS and CDL source requirements sheet

- **Role:** DS1
- **Spec created:** 2026-11-14
- **Roadmap phase and task:** Phase 1, DS1: Write source requirements sheet for HLS and CDL

## Goal

Produce a concise, actionable requirements sheet for the Data Engineer (DE) specifying exactly what to fetch from HLS (Harmonized Landsat-Sentinel) and CDL (Cropland Data Layer) for the P0 MVP. This tells DE: which bands/variables, years, seasons, field subsets, quality flags/masks, output format, and what "a correct file looks like" for each source.

## Approach

Two sheets, one per source. Each sheet covers:

1. **Source and product** — what to retrieve, API or endpoint, product version.
2. **Spatial subset** — field bboxes + buffer, so we fetch only what we need.
3. **Temporal subset** — years, growing-season windows.
4. **Bands / variables** — exactly which bands (HLS) or class layers (CDL).
5. **Quality handling** — which quality flags and masks to apply, what to filter.
6. **Output format and delivery** — file format, naming, what the DE delivers to the DS.
7. **Size budget** — an estimate per field so the DE can scale across ~30–50 fields.
8. **Validation check** — what the DS will inspect on first pull to confirm the file is correct.

The sheets stay in the feature spec folder and are also placed at the repo root in `specs/source-requirements/` for the DE to reference easily.

## Files and tables created

| File | Purpose |
|---|---|
| `specs/features/2026-11-14-ds1-hls-cdl-requirements/plan.md` | This plan |
| `specs/features/2026-11-14-ds1-hls-cdl-requirements/requirements.md` | Requirements and acceptance criteria |
| `specs/features/2026-11-14-ds1-hls-cdl-requirements/validation.md` | How we'll verify the sheets are correct |
| `specs/features/2026-11-14-ds1-hls-cdl-requirements/hls-requirements-sheet.md` | HLS-specific sheet for the DE |
| `specs/features/2026-11-14-ds1-hls-cdl-requirements/cdl-requirements-sheet.md` | CDL-specific sheet for the DE |

(No code, tables or endpoints are created in this task — this is a pure specification task.)

## Steps (in order)

1. Draft the HLS requirements sheet: review PRD §6, tech-stack HLS section, roadmap Phase 1 details.
2. Draft the CDL requirements sheet: review PRD §6, tech-stack CDL section, roadmap Phase 1 details.
3. Write plan.md, requirements.md and validation.md for this feature spec.
4. Update the roadmap progress tracker.

## Dependencies and interfaces with other roles

- **Upstream:** Phase 0 must be done (field polygons exist so we know the bboxes). Assumes the primary demo field + test set (~30–50 fields) are available as GeoJSON in the repo.
- **Downstream (DE):** The DE uses these sheets to implement the extraction jobs. The sheets must be clear enough that the DE can extract without asking the DS repeatedly.
- **Downstream (DS1 myself):** I will later use the delivered data to build CDL crop-history features (Phase 3) and HLS vegetation features (Phase 5).

## Data size and subsets

Not applicable to a spec task, but the sheets must define the subset so the DE can budget:
- HLS: bounded to field bboxes × 2–3 growing seasons × 2–3 years. Single-field dev sample first.
- CDL: annual rasters clipped to field bboxes, 2008–2025 (or available years), accounting for the 30 m → 10 m resolution change in 2024.

## Risks and open questions

- HLS tile coverage for Story/Boone Counties — need to confirm which tiles cover the area.
- CDL year range — 2008 onwards is available; confirm 2025 is published.
- Real field polygons may not exist yet; assume we use the team-drawn demonstration polygons from Phase 0.