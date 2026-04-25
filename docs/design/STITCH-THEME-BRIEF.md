# Stitch Theme Brief: Styio Community Decision Desk

Design a compact operations theme for `styio-community`, a private workflow
console where maintainers approve syntax coordination tasks and dispatch them
to downstream repositories.

## Product Role

This is not a marketing page. It is a working decision desk. The first viewport
must show what requires action, where it will be sent, and which button moves
the workflow.

## Visual Goals

- Low-noise, high-contrast operational UI.
- Strong color signals for workflow states.
- Fewer words, larger decision signal.
- Dense but readable layout for repeated use.
- No decorative hero, cards-inside-cards, gradients, or visual filler.

## Required Signals

- Awaiting decision: amber attention.
- Approved: green ready state.
- Dispatched: blue delivery state.
- Rejected: red terminal state.
- Adapter route such as `styio -> styio-view` must be visible near the title.
- Primary facts should look more important than history and raw payloads.

## Components

- Left queue: compact record list with title, status, and target repo.
- Main panel: title, route, status pill, one-line decision summary.
- Key facts: maximum three tiles.
- Opinion field: visible but not dominant.
- Actions: approve, reject, dispatch with clear button priority.
- History/result: collapsed into short summaries.

## Theme Direction

Use a neutral paper background, ink text, clean borders, and saturated state
accents. The interface should feel like a control room for project governance,
not an issue tracker or documentation page.
