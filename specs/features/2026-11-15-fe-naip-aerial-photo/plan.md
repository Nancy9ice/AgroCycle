# Plan: Aerial photo of a demonstration field (NAIP)

- **Role:** fe (the API half is BE work, written by the frontend developer to unblock the team; BE owner to review)
- **Spec created:** 2026-11-15
- **Roadmap phase and task:** Phase 13 / 11: use DE's `naip_tiles` (Phase 12) as a sharper picture of a demo field

## Goal

DE loaded `naip_tiles`: an index of 45 per-field aerial photos (NAIP 2025, 0.6 m, red, green, blue, near-infrared) that stay in a private S3 bucket. Let a person look at one on the demo map, labelled with when it was taken and what it is not.

## Approach

- **API** (`api/core/imagery.py`, `api/db/imagery.py`, `api/routes/imagery.py`): `GET /fields/{id}/imagery` says whether there is a photo, its flight date(s), resolution and where it sits; `GET /fields/{id}/imagery/image.png` is the picture. The chip is read from S3, **checked against the sha256 in `naip_tiles`**, warped from UTM to longitude/latitude with a transparent edge, and sent as a PNG. Colours are not changed. A key outside `raw/naip/` is never read. A bad or mismatched chip is a visible 503, never a blank picture. With no S3 (file mode) the answer is "no photo".
- **Web** (`features/field/imagery.ts`, `use-field-imagery.ts`, `app/field-imagery/...`): the browser asks the Next server, which asks the API (its address stays private). The demo map shows an "Aerial photo" toggle only for a field that has one. While on, a caption gives the flight date(s) (two for a field cut from two flights), "one aerial photo from one day, not a crop map", the Observed-product label and the NAIP attribution.
- **Check for someone with credentials:** `uv run python -m api.check_imagery primary-001` reads the real index and chip, checks the checksum and writes the picture.

## Not in scope

Showing the photo on the profile or the printed brief; the NIR band (a false-colour or greenness view); the own-boundary map. NAIP's licence text is unconfirmed (DE's note), so check before the site goes public.
