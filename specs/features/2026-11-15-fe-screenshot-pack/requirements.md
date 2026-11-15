# Requirements: Screenshot pack and README

## Covers

PRD §13 (slides from real screenshots; distinguish implemented functionality from mock-ups), §16 ("every competition claim is supported by evidence", "the demo shows actual functionality"). Roadmap Phase 15.

## Inputs

A running web app (`next start`), optionally with the API.

## Outputs

`docs/demo/screenshots/NN-name.png` (desktop, full page), `docs/demo/README.md`, an updated root `README.md`.

## Acceptance criteria

1. One command captures at least 9 screenshots: home, field map, profile, evidence drawer, priorities, comparison (real result), comparison (preview), adviser brief, validation.
2. Every screenshot's caption states whether it is real, labelled sample or preview, and what it proves for which slide; preview shots keep their banner in frame.
3. The guide says which slides an app screenshot cannot serve (slide 4) and what the team must replace once real indicator outputs exist (slide 2 weather).
4. No screenshot shows a number or result that the app would not show to a user, and none is edited.
5. The guide lists the commands to reproduce the shots and the environment they need.
6. The root README no longer says `api/`, `engine/` or `web/` are placeholders, gives the run commands for the API and the web app, and lists the environment variables.
7. `npm run check` passes; the script lints and has no new dependency.

## Out of scope

The deck itself, the architecture and lineage diagrams, the scientific-method write-up, the video, real weather data.
