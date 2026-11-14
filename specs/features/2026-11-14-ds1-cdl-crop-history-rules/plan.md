# Plan: CDL crop history rules

- **Role:** DS1
- **Spec created:** 2026-11-14
- **Roadmap phase and task:** Phase 3, DS1: Write CDL crop history rules spec

## Goal

Define the rules that will turn raw CDL pixel data into meaningful crop history per field: which CDL codes map to which crop groups, what threshold makes a "dominant crop" for a year, and what pattern counts as a "rotation". These rules will be used by the DE to build the crop history table and by the decision engine in Phase 10.

## Approach

Write a short, versioned rules document covering three things:

1. **Class-code groups** — which CDL integer codes map to corn, soybeans, pasture, other crops, and non-crop.
2. **Dominant-crop rule** — what % of a field's pixels must be a single crop to label that year. Below the threshold, the year is marked as mixed/uncertain.
3. **Rotation rule** — how many years of corn-soybean alternation counts as a "rotation", and what counts as "continuous corn".

The rules are placeholders that feed into Phase 9 (strategy profiles) and Phase 10 (decision engine). They will be reviewed when expert feedback is available.

## Files, tables and endpoints

| File | Purpose |
|---|---|
| `specs/features/2026-11-14-ds1-cdl-crop-history-rules/plan.md` | This plan |
| `specs/features/2026-11-14-ds1-cdl-crop-history-rules/requirements.md` | Acceptance criteria |
| `specs/features/2026-11-14-ds1-cdl-crop-history-rules/validation.md` | How to verify |
| `specs/features/2026-11-14-ds1-cdl-crop-history-rules/cdl-crop-rules.md` | The rules document (main deliverable) |

Later, the DE will implement these rules in code and produce tables in ClickHouse.

## Steps (in order)

1. Research CDL class codes for the relevant crop types (corn, soybeans, oats, alfalfa, clover, grass/pasture, etc.)
2. Define the class-code groups with the specific integer codes.
3. Define the dominant-crop threshold (e.g. if >= X% of pixels are one crop, that is the dominant crop).
4. Define the rotation rule (e.g. corn and soybeans must alternate in at least N of the last M year-to-year transitions).
5. Define continuous corn, pasture and mixed rules.
6. Write plan.md, requirements.md and validation.md.
7. Update roadmap progress tracker.

## Dependencies and interfaces with other roles

- **Upstream:** Phase 0 (field polygons exist). Phase 1-2 (CDL data in ClickHouse). This spec can be written before those complete, but implementation needs the data.
- **Downstream (DE):** The DE implements these rules as code: class shares per field per year, dominant crop per year, crop sequence, rotation flag.
- **Downstream (DS1 - myself):** I will review the DE's output (primary field hand-check, sample of test fields, flags).
- **Downstream (Phase 9-10):** These rules feed the strategy profiles and decision engine.

## Data size and subsets

CDL data is small (~5-30 MB total for all fields and years). No size concerns.

## Risks and open questions

- CDL class codes: need to confirm the master list for the 2008-2025 period. Some codes may have changed between years.
- 30 m vs 10 m resolution change in 2024: the rules must account for this (use percentages, not pixel counts).
- The DE could not download 2024/2025 at 10 m (confirmed 30 m for all years). This simplifies things — all years are consistent at 30 m.
- No fields with oats, alfalfa or clover were found. The rules should still define those codes for when they appear.