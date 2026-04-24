# CEL-THEME

CEL-THEME is the current Styio Community visual language. It is based on
cel-shading: hard ink outlines, flat color fills, offset shadows, compact icon
controls, and playful but disciplined spacing.

## Palette

Core colors:

| Token | Value | Use |
| --- | --- | --- |
| `--cel-bg` | `#fafaf5` | Page background and input fill |
| `--cel-paper` | `#ffffff` | Cards, app bar, raised icon wells |
| `--cel-paper-deep` | `#f0f0ea` | Nested panels and reply surfaces |
| `--cel-ink` | `#1a1a2e` | Borders, text, default shadows |
| `--cel-muted` | `rgba(26, 26, 46, 0.66)` | Secondary metadata |
| `--cel-red` | `#e63946` | Language channel and primary action |
| `--cel-blue` | `#4ea8de` | Toolchain channel |
| `--cel-green` | `#2ecc71` | Showcase channel, submit actions, success states |
| `--cel-teal` | `#14b8a6` | Utility navigation actions |
| `--cel-yellow` | `#f1c40f` | All channel and broad highlights |
| `--cel-purple` | `#9b59b6` | Help channel |

Section fills:

| Token | Value | Use |
| --- | --- | --- |
| `--section-board-bg` | `--cel-paper` | Board showcase band and ray field |
| `--section-discussion-bg` | `--cel-bg` | Discussion browsing band |
| `--section-composer-bg` | `--cel-paper` | Composer band |

Channel aliases:

| Channel | Token | Color |
| --- | --- | --- |
| `LANGUAGE` | `--category-language` | `--cel-red` |
| `TOOLCHAIN` | `--category-toolchain` | `--cel-blue` |
| `SHOWCASE` | `--category-showcase` | `--cel-green` |
| `HELP` | `--category-help` | `--cel-purple` |
| `ANNOUNCEMENT` | `--category-announcement` | `--cel-yellow` |
| General fallback | `--category-general` | `--cel-ink` |

## Shape

- Use `3px` ink borders for controls, cards, chips, and panels.
- Keep control and chip radii near `10px`; larger panels can use `14px`.
- Cards are rectangular and grounded. Avoid pill-like containers except for
  compact metadata chips.
- Do not nest decorative cards inside other decorative cards.

## Shadows

- Use hard offset shadows, never blur shadows.
- Standard component shadow: `3px 3px 0 var(--cel-ink)`.
- Raised shell shadow: `4px 4px 0 var(--cel-ink)`.
- The top app bar is not a raised card. It stays sticky at the top with the
  page background fill and a single ink divider below it.
- Deep hero/panel shadow: `6px 6px 0 var(--cel-ink)`.
- Post cards use the current category color as the shadow color. This ties the
  card to its channel while preserving the black ink outline.
- Post card title hover and selected states should use the same category color
  as the card shadow.

## Controls

- Icon buttons are square, compact, and carry the action through icon shape and
  color.
- Filter buttons use icon plus uppercase text because the channel names are
  part of navigation.
- All post, publish, reply, and send actions use the submit color class
  `is-submit`, which maps to `--cel-green`. This keeps visible submission
  controls consistent even when their labels differ.
- Search is automatic, so the search field does not need a submit button.
- The app bar uses a showcase-style flat header: sticky at the top, no rounded
  card frame, no hard shadow, and one ink divider underneath. It keeps only
  global actions on the right. New post appears before refresh so the submit
  action remains primary.
- Refresh and detail-page back navigation use the default paper fill with black
  ink shadow so they read as neutral utility actions.
- Filter buttons keep their selected channel in the pressed state. The `ALL`
  button clears filtering and returns every channel button to the raised state.

## Inputs

- Reuse `iconField()` and `.icon-field` for icon plus input layouts.
- Single-line form rows use a small icon well beside the input.
- The icon well is `42px` square with a `3px` ink border and `3px` shadow.
- The icon well sits `2px` lower than the input top. Its shadow visually locks
  near the input inner baseline instead of matching full input height.
- Multi-line text areas keep the icon well small and top-aligned. Do not stretch
  the icon well to the full text area height.
- Input text is bold and practical. Placeholders should be muted, not decorative.

## Typography

- Use the system sans stack already defined in CSS.
- Main labels, buttons, chips, and headings use heavy weights.
- Use uppercase for channels and command-like controls.
- Keep letter spacing at `0`; the cel effect should come from shape, color, and
  shadow rather than tracked type.

## Layout

- Home pages should read as stacked bands, not one rushed column. Use
  full-width `.page-band` sections with flat background fills and shared inner
  width; do not rely on oversized decorative headings to create separation.
  Prefer color changes over heavy black divider rules between page bands.
- The board hero is a layered stage: background, rays, cards. The board stage
  itself has no outer frame; the ray field background should blend with the
  surrounding board band.
- The STYIO card burst is centered in its own layer. Rays align to the card
  burst center and remain adjustable as a separate layer.
- Speed lines should mix thin, medium, and heavy strokes with subtle opacity
  changes so the ray field feels drawn rather than mechanically repeated. Rays
  should extend beyond the visible board bounds so they appear to strike through
  the full screen instead of stopping near the cards.
- Board card colors may reuse channel accents. The `T` card uses Toolchain blue
  and the `Y` card uses the same yellow accent as `ALL`.
- The discussion area has no large outer card. Individual posts carry the
  border and category shadow.
- Filter navigation sits above search with clear vertical spacing.
- The composer stays below the discussion list.
- Comment and editor cards use a top-right title area by default. If a section
  also has an icon, keep that icon at the left of the heading row and manually
  align it with the right-side title instead of wrapping both in one container.
  Put local controls in a separate strip rather than crowding that title area.
- Thread previous/next controls sit directly between the content card and reply
  card without a drawn outer container. Pager buttons can stay paper-filled
  while their hard shadow inherits the current category color, giving them a
  lighter surface that still echoes the active thread. Disabled pager buttons
  may fade with opacity; the greyed-out state is part of the interaction
  language and should remain visibly inactive.
- Reuse `iconTitle()` and `.icon-title` for icon plus title layouts. The title
  marker and text should keep a clear `12px` gap so the marker reads as metadata
  instead of crowding the heading.

## Motion

- Interactions should feel snappy and physical.
- Hover can increase the hard shadow by `1px` to `2px` and shift the element
  slightly upward-left.
- Active states can compress with a tiny scale change and reduced shadow.
- Avoid slow fades, soft glows, and blurred effects.

## Icon Style

- Icons are stroke-based, rounded, and simple.
- Default icon stroke is `2.4`.
- Use the existing SVG symbol set for local consistency before adding another
  icon source.
- Heart, comment, and view icons should share stroke weight and chip treatment.
- Home post titles can carry one compact square marker: pinned posts use the
  pinned marker; normal posts use the channel icon in the channel color.

## Future Themes

Future style themes should document the same sections: palette, shape, shadows,
controls, inputs, typography, layout, motion, and icon style. Keep each theme
isolated by token names or a theme prefix so multiple visual systems can coexist
without rewriting components.
