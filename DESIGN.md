# Introspect dashboard: design system

The world: **a morning journal for your own body.** Black page, red for the brand, lime for *you*,
and the number that matters set like a headline in a journal. Open sections divided by space and hairlines,
not boxes. Decided 2026-11-26 (replaces the navy/orange/cream look, at the owner's request).

## Colour
Dark: black ground, **signal red** for the brand and every control, **electric lime** that pops for your own numbers.
(Changed 2026-11-26 at the owner's request: "red, black, and a colour that can pop out on them".)

| Role | Value | Use |
|---|---|---|
| ground / sheet / raised | `#0A0A0A` / `#111111` / `#191919` | window and sidebar / content sheet / overlays, hovers |
| line / rule / control | `#262626` / `#1E1E1E` / `#3A3A3A` | hairlines, slider track |
| ink / muted / faint | `#F3F2EE` / `#ABAAA4` / `#8C8B86` | text tiers, all ≥4.5:1 on the sheet |
| **red** | `#EE3124` (text `#FF5A4E`, tint 16%) | brand mark, primary buttons, segmented thumb, switches, tab and nav indicators, flagged days, "below your normal" |
| **lime** (CSS `--spruce`) | `#D2FF3C` (tint 14%) | readiness line, today, the what-if, "above your normal", focus ring |
| white | `#F3F2EE` | tomorrow's forecast marker, 7-day marker |

Red is the brand and also drift; lime is only ever *your* data, so a lime number always means "you".

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
