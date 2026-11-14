# Validation: CDL crop history rules

## Checks

| Requirement / criterion | How it will be verified | Evidence kept |
|---|---|---|
| 1. Class-code groups complete | Manual check against USDA CDL class code table | Table in rules doc |
| 2. Dominant-crop threshold defined | Check rules doc for a clear % threshold | Value recorded in results |
| 3. Rotation rule defined | Check rules doc for alternation rule | Rule recorded in results |
| 4. Continuous corn rule defined | Check rules doc | Rule recorded |
| 5. Pasture/hay rule defined | Check rules doc | Rule recorded |
| 6. Mixed rule defined | Check rules doc | Rule recorded |
| 7. Resolution handling documented | Check rules doc | Note recorded |
| 8. Rules are versioned | Check doc has version + date | Confirmed |

## Results (fill in after implementation)

- **Date completed:** 2026-11-14
- **What was run:** Manual self-review of the rules document
- **Passed:**
  - 1. Class-code groups: ✅ All relevant codes for Story/Boone listed
  - 2. Dominant-crop threshold: ✅ >= 60%
  - 3. Rotation rule: ✅ >= 7 of 10 year-to-year changes must be corn-soybean alternations
  - 4. Continuous corn rule: ✅ >= 8 of 11 years must be corn
  - 5. Pasture/hay rule: ✅ >= 8 of 11 years must be pasture/hay
  - 6. Mixed rule: ✅ >= 5 corn or soybean years, and none of the above
  - 7. Resolution handling: ✅ Noted (all years at 30 m, using percentages)
  - 8. Versioned: ✅ v1.0, 2026-11-14
- **Failed or skipped:** None
- **Evidence location:** `specs/features/2026-11-14-ds1-cdl-crop-history-rules/cdl-crop-rules.md`
- **Roadmap exit check met:** Yes — the rules spec covers class-code groups, dominant-crop threshold, and rotation rule as required.
- **Roadmap tracker updated:** Yes, 2026-11-14