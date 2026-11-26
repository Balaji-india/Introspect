# Pitch runbook: wHACKiest 2026 online ideathon (Sky-Flyers · Introspect · T-3)

**Format:** 5 min presentation (hard cutoff) + 2 min judges' Q&A. Slot every 10 min, zero buffer. PPT frozen.

## Before the slot (checklist from the official guidelines)
- [ ] Team leader (Balaji) messaged the panel coordinator, all 4 joined the panel group, confirmation sent
- [ ] Join the **waiting room 5 min early**, each person with their **Devnovate-registered email** and **real full name**
- [ ] **All 4 cameras ON** for the whole slot; **college ID cards** in hand
- [ ] Decide **one screen-sharer** (the laptop running the demo). Before the call, open: tab 1 the submitted PPT, tab 2 the dashboard
      at `http://127.0.0.1:8000` (already loaded, demo reset done)
- [ ] Run `demo.bat` **15 min before**; click "Reset demo"; check the voice button plays; close other apps, notifications off
- [ ] Stable internet (hotspot ready as backup); mic tested; share the **window**, not the whole screen
- [ ] Backup: if the live demo fails, play the demo part of our YouTube video (2:55–3:20)

## 5-minute plan (rehearse with a timer)
| Time | Who | What |
|---|---|---|
| 0:00–0:20 | Balaji | Slide 1: team, Track 3, one-line pitch |
| 0:20–1:05 | Speaker 2 | Slide 2: problem (114.2M wearables; 1 in 3 abandon; students' sleep and stress) |
| 1:05–1:40 | Speaker 2 | Slide 3: solution (5 parts) |
| 1:40–2:30 | Speaker 3 | Slides 4–5: stack + architecture (on-device zone, privacy gateway, AWS + ElevenLabs) |
| 2:30–4:00 | Speaker 4 | **Live demo** (click path below) |
| 4:00–4:40 | Speaker 3 | Slides 6–7: novelty table, impact targets, AWS credits fund the pilot |
| 4:40–5:00 | Balaji | Slide 8: business model, close: "Your data, your device, your insights." |

Assign names to the speaker slots tonight. Only switch slides with the arrow keys; no clicking around.

## Live demo click path (~90 s)
> Dashboard layout (redesign): **Simulate** buttons sit in the top bar; **Privacy** and **Ask your data** are one click
> away in the sidebar. Readiness is the big number top-right. Clicking a red dot or a flagged day opens its detail sheet.

1. **Dashboard top (10 s):** "Readiness 60, where 50 is *your* normal, not a population average. Here's today's brief." Click **Play brief**.
2. **Readiness chart (10 s):** "Red dots are days that drifted from this user's baseline. You can see the exam week."
3. **Why card (10 s):** "The why-engine found that late screen time costs this user about 29 minutes of sleep, with p below 0.001."
4. **What-if slider (15 s):** drag 0 → 150: "Tonight's choice changes tomorrow: screens off by 11 gives 56; two hours on the phone gives 45."
5. **Simulate → Bad night (15 s):** "Watch: a bad night just happened." A new red point appears and the brief changes to "take it easy".
6. **Consent → cloud narration ON (15 s):** "Nothing leaves the device until I consent. Now only these aggregates go to Bedrock: no dates, no raw data."
7. **Ask (10 s):** click "Why am I tired?" and read the answer.
8. Back to slides.

If any step lags, skip it and say the line anyway. Never debug live.

## Likely judge questions (answer in 15–20 s each)
- **"Is this real data?"** "The demo uses a synthetic user in the exact Fitbit export format, so nobody's private health data is exposed. The loader already reads the public Kaggle Fitbit dataset, and we validate on it next."
- **"How accurate is the forecast?"** "Early. On about 50 days it beats the personal-average baseline and roughly matches 'tomorrow equals today'. The real value now is the what-if: it's constrained so more late-night screen time can never predict a better tomorrow. Accuracy improves with more days per user."
- **"Correlation isn't causation."** "Agreed. We label insights as patterns with rho, p and n, only report |rho| ≥ 0.3 and p < 0.05, and use lagged drivers so cause comes before effect. Next step is n-of-1 experiments: try screens off for a week and measure."
- **"How is it private if you use Bedrock?"** "The privacy gateway sends only allow-listed aggregates, never raw series, ids or dates, and only after per-purpose consent. Any LLM sentence with a number that isn't in the facts gets rejected, and Guardrails block medical claims."
- **"Why not just use Fitbit or Oura?"** "Those lock you to their hardware and cloud, and none of them join body signals with screen time and your exam calendar. We work on a ₹1,500 band, on-device."
- **"Medical liability?"** "It's wellness, not diagnosis. Red flags say 'see a doctor', and Guardrails filter medical claims."
- **"How do you make money?"** "Freemium: ₹99/month Pro, and ₹300 per user per year for colleges and companies, who only see anonymised trends. We never sell data."
- **"What does AWS do?"** "Bedrock with Claude Haiku and Guardrails for the brief; Lambda, API Gateway, Cognito, DynamoDB consent ledger, EventBridge for the 7 AM brief, S3 + KMS backup. Our $243 credits cover the build and the 30-student pilot."
- **"What's left for the 24-hour build?"** "Health Connect and HealthKit importers, real-data validation, deploying the SAM stack, the Next.js PWA, voice in Hindi."
