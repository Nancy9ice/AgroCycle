# Plan: Architecture and lineage diagrams for slide 4

- **Role:** fe (written for the team; DE, DS2 and BE should check the status marks for their parts)
- **Spec created:** 2026-11-15
- **Roadmap phase and task:** Phase 15, claim check and slide-deck prep (slide 4, `PRD.md` §13: architecture diagram and data-lineage diagram)

## Goal

Two figures a cold reader can use: where the data goes and what is built, and how one NASA observation becomes a statement on screen. The PRD asks the deck to "clearly distinguish implemented functionality from mock-ups and future work", so built versus not built is drawn on the shapes.

## Approach

- **One claim per figure.** Architecture: the path and its status. Lineage: one indicator (growing degree days), traced to the three things the engine's rules can do with it.
- **Status from the tracker, not from memory.** Each box's status is taken from `specs/roadmap.md`; the figure is a snapshot and says so in `docs/diagrams/README.md`.
- **Every arrow is labelled**, and dashed arrows are connections that do not exist yet.
- **Real rule numbers.** The lineage figure uses the thresholds in `engine/rules/strategy_rules.py` and `transform/indicators/climate.py`.
- **Generated, so status changes are one word.** `docs/diagrams/build.py` (standard library only) writes the SVGs; PNGs are rendered with headless Chrome.

## Files

`docs/diagrams/build.py`, `architecture.svg`, `lineage.svg`, `.png` renders, `README.md`.

## Risks and open questions

- Status goes stale as teammates finish work; the README says how to update.
- The lineage figure shows one indicator; the others follow the same path but not all feed a rule.
