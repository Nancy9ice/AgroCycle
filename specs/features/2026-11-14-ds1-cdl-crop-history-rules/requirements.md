# Requirements: CDL crop history rules

## Covers
- **PRD requirements:** FR-02 (Crop history), FR-06 (Data adequacy), NFR-02 (Explainability), NFR-03 (Auditability)
- **Roadmap exit check satisfied:** "DS1 first writes a short rules spec: the class-code groups, the dominant-crop threshold, and the rotation rule"

## Inputs

| Item | Source | Notes |
|---|---|---|
| CDL class codes | USDA NASS documentation | Integer codes mapping to crop types (2008-2025) |
| Field polygons | Phase 0 output | 45 fields (1 primary, 44 test) in Story/Boone Counties |
| Resolution info | Phase 0 output | All years at 30 m (confirmed by DE) |

## Outputs

| File | Contents |
|---|---|
| `cdl-crop-rules.md` | Versioned rules document with: class-code groups, dominant-crop threshold, rotation rule, continuous corn rule, pasture rule, mixed rule, resolution handling note |

## Acceptance criteria

Each must be testable.

1. **Class-code groups are complete:** Every CDL integer code that could appear in Story/Boone Iowa is assigned to a group (corn, soybean, other-crop, pasture-hay, non-crop) or explicitly noted as "not expected".
2. **Dominant-crop threshold is defined:** A single percentage threshold is stated (e.g. ">= 60% of pixels must be the same crop class"). Years below this are marked "mixed/uncertain".
3. **Rotation rule is defined:** The rule for calling a field a "rotation" is stated in terms of year-to-year corn-soybean alternations (e.g. "at least N of the last M year-to-year changes must be alternations").
4. **Continuous corn rule is defined:** The rule for "continuous corn" is stated separately.
5. **Pasture/hay rule is defined:** The rule for "pasture/hay" is stated separately.
6. **Mixed rule is defined:** The catch-all for fields that do not fit the above.
7. **Resolution handling is documented:** A note on how to compare years across the 30 m resolution (all years consistent).
8. **Rules are versioned:** The document includes a version number and date.

## Evidence labels, scale and limitations to preserve

- **CDL:** evidence type = `Classified output`. Scale = 30 m for all years. Limitations: classified product, not ground truth. Resolution consistent across all years (confirmed 30 m).
- **Crop sequence:** evidence type = `Derived indicator` (derived from CDL). Scale = field-level aggregate. Limitations: depends on CDL accuracy; mixed/uncertain years are flagged.

## Out of scope

- Writing implementation code. The DE implements these rules.
- HLS features (Phase 5).
- Strategy comparison rules (Phase 9).
- Decision engine logic (Phase 10).