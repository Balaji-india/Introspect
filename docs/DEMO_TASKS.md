# Demo tasks for tomorrow's pitch (do them in order)

Deadline: demo-ready by tonight. Pitch at 11:00 AM; demo slot is about 90 seconds inside a 5-minute talk.
After **each** task: `pytest -q` passes, the dashboard loads, then commit. If a task runs long, stop and move on:
P0 is mandatory, P1 is strongly wanted, P2 only if there's spare time.

---

## P0: reliability (must have)

### T1. One-command start
- Add `scripts/start_demo.py`: checks imports, frees or chooses port 8000, starts uvicorn, waits for `/api/health`,
  then opens `http://127.0.0.1:8000` in the default browser. Print a clear error if a dependency is missing.
- Add `demo.bat` (Windows) and `demo.sh` that activate `.venv` if present and run it.
- **Done when:** a fresh terminal plus `demo.bat` opens a working dashboard in under 10 seconds.

### T2. Instant what-if slider
- `/api/forecast` retrains LightGBM on every slider move. Cache the trained model per dataset (train once, then
  predict only). Keep the response format the same.
- **Done when:** dragging the slider from 0 to 180 updates the number with no visible lag (under 150 ms per call locally).

### T3. Demo reset
- `POST /api/demo/reset`: clears `.introspect/` state (consent back to defaults), restores the default sample data,
  clears caches. Add a small "Reset demo" link in the dashboard footer.
- **Done when:** after clicking around, Reset puts everything back to the first-load state.

---

## P1: wow moments (strongly wanted)

### T4. Scenario simulator ("watch it detect live")
- Extend `synthetic.generate(...)` with `scenario` in {`normal`, `exam_week`, `bad_night`} (current default = today's data).
  - `normal`: no exam week, no planted bad night.
  - `exam_week`: exam week ends **yesterday**, with higher late-screen time.
  - `bad_night`: the planted bad night is **last night** (latest day), so today's brief changes.
- `POST /api/demo/scenario {"scenario": "..."}` writes the data to `.introspect/demo_data/`, points the pipeline at it,
  and clears caches. All endpoints then use the active dataset (keep `config.DATA_DIR` as the default).
- Dashboard: a "Simulate" card with three buttons; after a click, re-fetch everything and re-render the charts
  (destroy old Chart instances first).
- **Done when:** clicking "Bad night" makes a new red flagged point appear on the latest day and the brief now
  mentions the sleep / resting-HR / HRV drift and suggests taking it easy. Add tests for each scenario.

### T5. Privacy gateway, made visible
- Dashboard card "What leaves this device": shows `GET /api/facts/cloud_narration`.
  Without consent it shows a lock and "Blocked: no consent". Toggling "Purpose: cloud narration" in the consent
  vault refreshes the card to show the exact JSON of aggregate facts (no dates, no ids, no raw series).
- **Done when:** toggling consent visibly flips the card between blocked and the facts JSON.

### T6. Voice brief that always works
- If ElevenLabs is configured, keep the current `POST /api/brief/voice`.
- Otherwise fall back to the browser's `speechSynthesis` to read the brief, and label the button
  "▶ Play brief (device voice · ElevenLabs when key set)".
- **Done when:** the button always produces audio offline, and with a key plus consent it plays ElevenLabs audio.

### T7. Ask your data
- `POST /api/ask {"question": "..."}`: answers only from privacy-gateway facts.
  - If Bedrock is enabled and `cloud_narration` consent is on: send the question plus facts to Bedrock (same system rules
    as `narrate.py`), and run `narrate.grounded()` on the answer (fall back if it fails).
  - Otherwise use a deterministic intent matcher over facts: sleep, readiness/tired, why, tomorrow/forecast, steps, help.
  - Return `{answer, source: "bedrock"|"on-device"}`.
- Dashboard: an input box with 3 chips: "Why am I tired?", "How will tomorrow be?", "What should I change?".
- **Done when:** all 3 chips give sensible, grounded answers offline. Add tests.

---

## P2: only if time is left

### T8. Live Bedrock check (uses our AWS credits)
- In the AWS console (us-east-1), enable model access for Anthropic Claude 3 Haiku in Bedrock. Run `aws configure`.
  Load `.env` via python-dotenv. Set `INTROSPECT_USE_BEDROCK=1` and toggle `cloud_narration` consent.
- Show a status pill in the header: "Bedrock: live" / "Bedrock: off (on-device)".
- **Done when:** `/api/brief` returns `source: "bedrock"` with real AWS. If access isn't granted in time, leave it off;
  the fallback is fine.

### T9. Upload your own Fitbit export
- `POST /api/upload` accepts the Kaggle Fitbit CSVs (`dailyActivity_merged.csv`, `sleepDay_merged.csv`,
  optional `heartrate_seconds_merged.csv`) into `.introspect/upload/` and switches the active dataset. Missing
  screen-time/HRV is fine; insights just get fewer.

### T10. README
- Update the README "What works today" table and the endpoint list with whatever was finished. Keep it honest.

---

## Don't
- Don't touch the PPT or add claims to the UI that the deck or code can't back up.
- Don't add CDN scripts, a build step, or Next.js tonight.
- Don't leave the app needing internet or keys to run.
