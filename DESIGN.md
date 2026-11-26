# Introspect dashboard: design system

The world: **a morning journal for your own body.** Quiet paper, one ink, one living colour for *you*,
and the number that matters set like a headline in a journal. Open sections divided by space and hairlines,
not boxes. Decided 2026-11-26 (replaces the navy/orange/cream look, at the owner's request).

## Colour
| Role | Value | Use |
|---|---|---|
| ground | `#F4F4F1` | window, sidebar (second neutral layer) |
| sheet | `#FFFFFF` | the page sheet the content sits on |
| raised | `#F7F7F4` | hover rows, inputs, quiet fills |
| line / rule | `#E4E4DF` / `#EDEDE9` | hairlines |
| ink / muted / faint | `#121411` / `#5B5E57` / `#6E716A` | text tiers, all ≥4.5:1 on the sheet |
| **spruce** (you) | `#1F5A47` (tint `#E3EEE9`) | readiness line, today, selection, primary action |
| **amber** (tonight) | `#B86A12` text, `#E08A2C` marks (tint `#FBEEDC`) | what-if, tomorrow's forecast |
| **coral** (drift) | `#C23B22` (tint `#FBE6E1`) | flagged days only |

At most these three hues on a screen. Colour goes on data and state, never on chrome.

## Type
- **Geist** (variable, vendored): every label, control, table and number. Tabular figures on all data.
  Scale 12 / 13 / 14 / 15 / 17 / 22 px; weights 400 / 500 / 600.
- **Instrument Serif** (vendored): the voice. Only the greeting, view titles and the lead readiness figure.
  Greeting 44px/1.05, tracking -0.015em; lead figure 112px.
- No uppercase tracked labels, no eyebrows above headings.

## Shape and depth
Radius: 10px controls, 14px the sheet, 999px for segmented controls and chips. No resting shadows; only
overlays float (menu, sheet, toast, tooltip) with an offset, soft shadow.

## Motion
`--ease-out: cubic-bezier(.23,1,.32,1)`, `--ease-io: cubic-bezier(.77,0,.175,1)`, `--ease-drawer: cubic-bezier(.32,.72,0,1)`.
Press 140ms scale(.97). Indicators (nav, segmented, tabs) slide 260ms ease-io. View change: a View Transition
crossfade with a 6px rise, 220ms. Charts draw once on a data change (700ms ease-io). Numbers count 500ms.
Reduced motion keeps opacity, drops travel.

## Signature
**The personal-normal ruler:** one 0–100 scale with your normal band (45–55) shaded; today, your 7-day average
and tomorrow's forecast are marks on it. It explains "50 = your normal" without a sentence.
