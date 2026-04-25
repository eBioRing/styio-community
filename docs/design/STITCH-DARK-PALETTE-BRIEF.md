# Stitch Dark Palette Brief: Styio Community Console

Design a dark-first color palette for the existing `styio-community` operations
console. Choose the palette freely.

## Context

The app is a working governance console for repository coordination decisions.
Users read it for long periods, so the dark mode must be calm, readable, and
not visually exhausting.

## Required Output

Generate a single desktop screen that demonstrates only the dark palette and
the existing console components:

- top app bar
- left decision queue
- central decision panel
- status labels: awaiting, approved, dispatched, rejected
- three action buttons: approve, reject, dispatch
- textarea and compact history/result blocks

## Palette Direction

Let Stitch choose the color system. Do not follow any preset brand colors from
previous iterations. The only requirement is that the result must be readable,
pleasant in a dark room, and clearly distinguish workflow states.

Avoid orange, red-orange, rust, and brick tones as dominant accents. If warning
needs a warm signal, keep it restrained and secondary, not the main visual
identity.

## Constraints

- Do not use gradients, hero sections, illustrations, profile photos, or extra
  navigation.
- Prioritize readability and visual comfort over drama.
- Produce reusable color tokens visible in the generated HTML/CSS.
