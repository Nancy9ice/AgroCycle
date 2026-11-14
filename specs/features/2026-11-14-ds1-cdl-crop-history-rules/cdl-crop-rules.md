# CDL Crop History Rules

**Version:** v1.0
**Date:** 2026-11-14
**Author:** DS1 (Hannah)
**Status:** Draft for Phase 3 implementation

---

## Purpose

These rules define how raw CDL pixel data is converted into per-field crop history: what each crop code means, what counts as the "dominant crop" for a year, and what patterns count as "rotation", "continuous corn", "pasture/hay" or "mixed". They are used by the DE to build the crop-history table and feed into Phase 9 (strategy profiles) and Phase 10 (decision engine).

---

## 1. Class-code groups

CDL uses integer codes to identify crop types. The codes relevant to Story and Boone Counties, Iowa are grouped as follows:

### Corn group

| Code | Crop |
|---|---|
| 1 | Corn |
| 12 | Sweet Corn |
| 13 | Pop or Ornamental Corn |
| 225 | Dbl Crop WinWht/Corn |
| 226 | Dbl Crop Oats/Corn |

### Soybean group

| Code | Crop |
|---|---|
| 5 | Soybeans |
| 26 | Dbl Crop WinWht/Soybeans |
| 239 | Dbl Crop Soybeans/Cotton |
| 240 | Dbl Crop Soybeans/Oats |

### Small grains and cover crops (for strategies B and C)

| Code | Crop |
|---|---|
| 28 | Oats |
| 36 | Alfalfa |
| 37 | Other Hay/Non Alfalfa |
| 58 | Clover/Wildflowers |
| 59 | Sod/Grass Seed |
| 176 | Grass/Pasture |
| 171 | Evergreen Trees (for windbreaks, not crop) |

### Non-crop (exclude from analysis)

| Code | Land cover |
|---|---|
| 0 | Background / No data |
| 61 | Fallow/Idle Cropland |
| 111 | Open Water |
| 121 | Developed/Low Intensity |
| 122 | Developed/Medium Intensity |
| 123 | Developed/High Intensity |
| 124 | Developed/Open Space |
| 131 | Barren |
| 141 | Deciduous Forest |
| 142 | Evergreen Forest |
| 143 | Mixed Forest |
| 152 | Shrubland |
| 176 | Grassland/Pasture (if not pasture class) |
| 190 | Woody Wetlands |
| 195 | Herbaceous Wetlands |

### Unclassified / other

Any code not listed above: mark as `other-crop` and flag for review. Most of these (e.g. wheat, sorghum, rice) are uncommon in Story/Boone but should not crash the pipeline.

---

## 2. Dominant-crop threshold

For each field and each year:

- Calculate the percentage of total field pixels occupied by each CDL class.
- **If one class-code group (from Section 1) occupies >= 60%** of the field's pixels, label that year with that group (e.g. "corn", "soybeans", "oats", "alfalfa").
- **If no group reaches 60%**, label the year as `mixed/uncertain`.
- **If no-data (code 0) pixels** exceed 20% of the field, flag the year as `low-confidence` and exclude it from rotation analysis.

> **Note:** The 60% threshold is a starting point. It may be adjusted after reviewing the DE's output. A lower threshold (e.g. 50%) would label more years with a crop but with less confidence. A higher threshold (e.g. 75%) would flag more years as mixed/uncertain.

### Resolution handling

All years (2008-2025) are at **30 m** resolution, as confirmed by the DE. This means:
- Use **percentages** not raw pixel counts.
- No resolution adjustment is needed between years.
- Record the resolution in the manifest for provenance.

---

## 3. Rotation rule

A field is classified as a **rotation** if:

> Corn (or sweet corn/pop corn) and soybeans alternate in at least **7 of the last 10 year-to-year transitions**.

A "year-to-year transition" is the change from one year to the next:
- A transition counts as an **alternation** if year N is corn-group and year N+1 is soybean-group, or vice versa.
- If either year is `mixed/uncertain`, that transition is not counted (neither for nor against).

**Example check for primary-001:**
Sequence: `S C S C S C S C S C S` (11 years, 10 transitions)

| Transition | Change | Alternation? |
|---|---|---|
| 2015->2016 | S->C | Yes |
| 2016->2017 | C->S | Yes |
| ... | ... | Yes (all 10) |

10 out of 10 alternations >= 7. **Passes as rotation.** ✅

---

## 4. Continuous corn rule

A field is classified as **continuous corn** if:

> Corn-group crops occupy at least **8 of the 11 years**, AND the field does NOT meet the rotation rule.

---

## 5. Pasture/hay rule

A field is classified as **pasture/hay** if:

> Pasture/hay/grass codes (176, 37, 58, 59) occupy at least **8 of the 11 years**, AND the field does NOT meet the rotation or continuous corn rules.

---

## 6. Mixed rule

A field is classified as **mixed** if:

> The field has at least **5 years of corn-group or soybean-group** crops, AND it does NOT meet the rotation, continuous corn, or pasture/hay rules.

---

## 7. Rule application order

Apply rules in this order:

1. Check **rotation** first (most specific).
2. If not rotation, check **continuous corn**.
3. If not continuous corn, check **pasture/hay**.
4. If none of the above, check **mixed**.
5. If the field has fewer than 5 corn/soy years and does not meet pasture/hay, label as `other`.

This ensures a field is labelled with the most specific applicable category.

---

## 8. Evidence and provenance

Each output (dominant crop per year, crop sequence, field class) must include:

- CDL product version and year
- Resolution (30 m)
- Rule version (this document: v1.0)
- Number of valid pixels and percentage for the dominant class
- Flag for any year marked `mixed/uncertain` or `low-confidence`

---

## 9. Open questions for future review

- The 60% dominant-crop threshold needs validation against real data. It may be adjusted in Phase 14.
- The 7-of-10 alternation rule for rotation is conservative. Fewer alternations (e.g. 5-of-10) would capture more fields as rotations but with less certainty.
- Expert review from an Iowa agricultural adviser is needed but not available for the MVP. These rules are labelled "not expert-reviewed".