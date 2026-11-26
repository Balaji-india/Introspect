# Introspect: product context

**What it is.** A private, on-device "AI twin" for personal health data. It merges wearable, phone-screen-time
and calendar data, learns the user's own baseline, flags drift, explains why (lagged correlation), forecasts
tomorrow's readiness with a what-if on tonight's screen time, and gives a short daily brief. Raw data never
leaves the device; only allow-listed aggregates pass a privacy gateway, and only with per-purpose consent.

**Who uses the dashboard.** A student (the pilot is 30 students) who glances at it once in the morning, on a
laptop or phone, to answer: *how ready am I today against my own normal, and what should I do tonight?*
Right now it is also shown live to ideathon judges in a 90-second, screen-shared demo.

**Surface mode.** Operate (an app screen worked in daily), with a little Experience in the first screen,
because the demo has to land in seconds.

**Jobs, most frequent first.** Read today's readiness and brief; try tonight's what-if; see which habit moves
the numbers; inspect a flagged day; decide what leaves the device (consent); ask a question of the data.

**Constraints (from CLAUDE.md).** Offline first: one HTML file, fonts and scripts vendored, no CDN. Honest
numbers: everything shown comes from the local API's models, nothing invented. Wellness, not diagnosis: no
medical claims. Don't claim the planned features (Next.js PWA, SQLCipher, Health Connect) are done.

**Success.** A judge thinks "this is a real, well-designed product" within the first screen. The demo path
(brief → chart → why → what-if → simulate a bad night → consent → ask) never breaks.

**What would feel wrong.** A generic SaaS template: a KPI-card row, cards around everything, gradients,
glass, a coloured sidebar, hero metrics without meaning, motion for its own sake.
