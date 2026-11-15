# Diagrams for slide 4

Two figures for slide 4 of the deck (architecture and data lineage, `PRD.md` §13). Each makes one claim.

| File | Claim it makes |
|---|---|
| [`architecture.svg`](architecture.svg) / `.png` | Where the data goes from NASA and USDA sources to the screen, and **which parts are built and which are not** |
| [`lineage.svg`](lineage.svg) / `.png` | One indicator traced end to end: a NASA observation becomes growing degree days, then a gap to the Iowa trial site, which the decision engine's rules turn into no effect, a caveat, or withholding every outcome |

The SVGs are vector (use them in the deck if it takes SVG); the PNGs are 2560 px wide for slides.

## What the marks mean

- **Solid green:** built and tested. **Amber:** built but not fully exercised. **Dashed red:** not built.
- An arrow's label says what moves along it. Dashed arrows are connections that do not exist yet.

## Status is a snapshot, written from the tracker

Status comes from `specs/roadmap.md` as of 2026-11-15:

- Sources, ingest, S3 and ClickHouse are done. Indicators, crop history, lineage and HLS valid-pixel counts are loaded.
- **transform** is amber: indicators and crop-history rules are built; HLS vegetation features (NDVI) are not.
- **FastAPI** is amber: the engine and endpoints are built and tested, but the ClickHouse reader has only run against a fake database, not the live one (`python -m api.check_clickhouse`).
- Not built: HLS greenness features, Marsden tables in ClickHouse, the evidence and lineage endpoints, polygon upload.

When the live ClickHouse check passes, change `FastAPI` to `built` in `build.py`, re-run, and re-export the PNGs:

```bash
python3 docs/diagrams/build.py
for n in architecture lineage; do
  chrome --headless=new --hide-scrollbars --force-device-scale-factor=2 --window-size=1280,560 \
    --screenshot="docs/diagrams/$n.png" "file://$PWD/docs/diagrams/$n.svg"
done
```

## Accuracy notes

- The lineage figure uses the real rule numbers from `engine/rules/strategy_rules.py` (300 degree-days; unknown; a missing required indicator) and the real indicator definition from `transform/indicators/climate.py` (base 10 °C, cap 30 °C, 90 % valid-day threshold). If those change, edit `lineage()` in `build.py`.
- The "11 % low" rainfall figure is DS2's own comparison with the Iowa station record (`docs/sources/ds2-first-pull-review-2026-11-14.md`).
- Do not describe this as a validated pipeline. `docs/demo/README.md` and the validation page say what has and has not been checked.
