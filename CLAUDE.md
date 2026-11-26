# CLAUDE.md: Introspect (team Sky-Flyers, wHACKiest 2026, Track 3)

## What this project is
Introspect is a private, on-device "AI twin" for personal health data. It merges wearable, phone and calendar
data, learns the user's own baseline, flags drift, explains *why* (for example "late screen time costs you about 29 min of sleep"),
forecasts tomorrow's readiness with a what-if, and gives a short daily brief. Raw data never leaves the device; only
aggregate facts pass through a privacy gateway, and only with consent.

## Why we're working on it right now
**Live online ideathon pitch: tomorrow 11:00 AM.** We get **5 minutes in total** (slides + live prototype), then 2 minutes of Q&A,
with a hard cutoff. The PPT is frozen: no changes are allowed. The job is to make the **live demo smooth, reliable and
impressive in about 90 seconds**. Read `docs/DEMO_TASKS.md` for the task list and `docs/DEMO_RUNBOOK.md` for how it will be shown.

## Hard rules
1. **Never break the demo.** After every task: `pytest -q` must pass, and `uvicorn api.main:app` plus the dashboard must load.
2. **Offline first.** Everything must work with no internet and no API keys. AWS Bedrock and ElevenLabs are optional
   upgrades that fall back gracefully (they already do in `narrate.py` and `voice.py`; keep that pattern).
3. **Never commit secrets.** Keys go in `.env` (gitignored). Never print keys in logs or the UI.
4. **Don't contradict the frozen deck.** The deck says: personal baseline (robust z), Isolation Forest, LightGBM readiness
   forecast, lagged correlation + SHAP "why", privacy gateway, consent vault, Bedrock (Claude Haiku) + Guardrails,
   ElevenLabs voice, MCP endpoint, AWS Lambda/API Gateway/Cognito/DynamoDB/EventBridge/S3+KMS, $243 AWS credits.
   Next.js PWA, SQLCipher and Health Connect are planned for hack day; don't claim they're done.
5. **Wellness, not diagnosis.** No medical claims anywhere in UI text.
6. **Honest numbers.** Never hard-code fake metrics in the UI; show what the models actually compute.
7. Small, focused commits with clear messages. Commit after each finished task.

## Repo map
```
introspect/        core library
  synthetic.py     60-day synthetic user in Fitbit export format (planted patterns + one bad night at n-4)
  ingest.py        Fitbit/Kaggle export + screen_time/calendar/checkins CSV -> daily timeline
  features.py      lags, rolling features
  baseline.py      robust z vs previous 28 days (median + IQR), readiness 0-100 (50 = your normal), Isolation Forest
  why.py           lagged Spearman + effect size; |rho|>=0.3 & p<0.05; actionable drivers ranked first
  forecast.py      LightGBM residual-on-persistence with monotonic constraints; what-if on tonight's screen time
  privacy.py       allow-listed aggregate facts; release(facts, purpose) needs consent
  consent.py       local JSON consent vault (.introspect/consent.json)
  narrate.py       template brief, or Bedrock Converse + Guardrails with a number-grounding check
  ask.py           "Ask your data": on-device intent matcher over gateway facts (Bedrock optional, grounded)
  voice.py         ElevenLabs TTS (needs key + 'voice_brief' consent)
  pipeline.py      run(data_dir) -> timeline, anomalies, insights, forecast, facts, brief
api/main.py        FastAPI; serves dashboard at / and /static; Lambda handler via Mangum
dashboard/index.html  single-file dashboard (Chart.js vendored at dashboard/vendor, works offline)
mcp_server/server.py  MCP tools get_daily_summary / get_insights (need 'mcp_access' consent)
infra/template.yaml   AWS SAM template (not deployed)
scripts/start_demo.py one-command demo start (demo.bat / demo.sh); scripts/run_demo.py CLI demo
tests/                33 pytest tests (conftest forces cloud features off)
```

## Existing API
`GET /api/health` · `/api/timeline` · `/api/anomalies` · `/api/insights` · `/api/forecast?screen_min=&exam_tomorrow=` ·
`/api/brief` · `POST /api/brief/voice` · `GET|POST /api/consent` · `GET /api/facts/{purpose}` (403 without consent) · `POST /api/ask` ·
`GET|POST /api/demo/scenario` · `POST /api/demo/reset` · `GET /` dashboard

## Setup (Windows PowerShell)
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1          # if blocked: Set-ExecutionPolicy -Scope Process Bypass
pip install -r requirements.txt
pytest -q
uvicorn api.main:app --reload       # http://127.0.0.1:8000
```
macOS/Linux: `source .venv/bin/activate`.

## Optional cloud (only if time allows; must keep fallbacks)
`.env`: `INTROSPECT_USE_BEDROCK=1`, `AWS_REGION=us-east-1`, `BEDROCK_MODEL_ID=anthropic.claude-3-haiku-20240307-v1:0`,
`ELEVENLABS_API_KEY=...`. AWS credentials come from `aws configure`. Cloud purposes also need consent toggled in the dashboard.
`config.py` reads `.env` itself at import (no python-dotenv needed; real environment variables win).

## Style
Python 3.11+, type hints, small functions, no new heavy dependencies. Dashboard: keep it a single HTML file with the
existing palette (navy #1B1F6B, orange #FD9B36, rust #C2410C, cream #F8F2E4). No CDN links (the demo must work offline).
