# Paste this into Claude Code (run it from inside the `introspect` folder)

---

You are working on **Introspect**, our wHACKiest 2026 hackathon prototype. We present it **live tomorrow at 11:00 AM**,
and the judges want a live prototype demo of about 90 seconds inside a 5-minute pitch.

First, read these files fully: `CLAUDE.md`, `docs/DEMO_TASKS.md`, `docs/DEMO_RUNBOOK.md`, `README.md`, then skim
`introspect/`, `api/main.py` and `dashboard/index.html`.

Then:
1. Set up the environment (Windows PowerShell: `python -m venv .venv`, `.venv\Scripts\Activate.ps1`,
   `pip install -r requirements.txt`) and run `pytest -q`. All 12 tests must pass before you change anything.
   Tell me if they don't.
2. Show me a short plan (5–10 lines) for tasks T1–T7 in `docs/DEMO_TASKS.md`, then start immediately.
   Don't wait for approval unless something in the plan is risky.
3. Work through the tasks **in order: P0 (T1–T3), then P1 (T4–T7)**. For each task:
   - implement it, add or extend tests, run `pytest -q`
   - start the server and check the dashboard still loads and the new feature works
   - commit with a clear message (e.g. `feat(demo): scenario simulator`)
   - give me a 2-line update: what's done, how to see it
4. Follow every hard rule in `CLAUDE.md`: offline-first, no secrets committed, no CDN scripts, nothing that
   contradicts the frozen deck, no medical claims, no fake numbers.
5. Only do P2 (T8–T10) if P0 and P1 are finished and stable. For T8 (live Bedrock), ask me before running anything
   that uses AWS credentials.
6. At the end:
   - run the full demo click path from `docs/DEMO_RUNBOOK.md` yourself (start → reset → each step) and fix anything slow or broken
   - update `README.md` honestly
   - give me a final summary: what works, the exact command to start the demo, and anything to avoid clicking live.

If something is ambiguous, pick the option that keeps the live demo simplest and most reliable, and tell me what you chose.
Speed matters, but **a demo that never breaks beats a demo with more features.**

---

After it finishes: `git push` so the whole team has the same version.
