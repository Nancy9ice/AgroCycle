# Plan: One meaning for the crop letter L

- **Role:** fe (touches DS1/DE code at the team's request)
- **Spec created:** 2026-11-15
- **Roadmap phase and task:** Phase 10/11, crop-code vocabulary open item from the real-data pass

## Goal

`L` meant *low confidence* in DS1's rules and `crop_rotation.sequence`, and *clover* in the field notes and the web app. The team decided `L` stays clover. DS1's low-confidence year gets a new letter, `U` (unclassified), so an unclassified year can never read as clover.

## Approach

- `transform/crop_history/rules.py`: `TOKEN_LOW_CONFIDENCE = "U"`. Status names (`low_confidence`) are unchanged.
- Tests and the DE requirements line updated to match. API comments and README no longer call `L` a clash.
- No data reload: the live `crop_history` has no low-confidence year (all 495 field-years are `ok`, per DE's validation), so no stored sequence contains the old `L`. A future load writes `U`.

## Not changed (still open)

`P`, `N`, `M` exist only in DS1's list; `G`, `H` only in the web app's; DS1 spaces the letters. The API keeps reading the crop sequence from the committed notes until those are aligned.
