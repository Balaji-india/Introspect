"""Introspect API (FastAPI). Runs locally, or on AWS Lambda behind API Gateway via Mangum.

    uvicorn api.main:app --reload        # then open http://127.0.0.1:8000
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from introspect import __version__, baseline, config, consent, features, forecast, ingest, pipeline, privacy, voice

ROOT = Path(__file__).resolve().parent.parent
app = FastAPI(title="Introspect API", version=__version__,
              description="Private personal-intelligence twin: baseline, anomalies, why-engine, forecast, brief.")


@lru_cache(maxsize=1)
def _result():
    return pipeline.run(config.DATA_DIR)


@lru_cache(maxsize=1)
def _frame():
    return baseline.compute_baseline(features.add_features(ingest.build_timeline(config.DATA_DIR)))


@app.get("/api/health")
def health():
    return {"status": "ok", "version": __version__, "bedrock": config.USE_BEDROCK,
            "elevenlabs": bool(config.ELEVENLABS_API_KEY)}


@app.get("/api/timeline")
def timeline():
    return _result()["timeline"]


@app.get("/api/anomalies")
def anomalies():
    return _result()["anomalies"]


@app.get("/api/insights")
def insights():
    return _result()["insights"]


@app.get("/api/forecast")
def what_if(screen_min: float | None = None, exam_tomorrow: int = 0):
    """Tomorrow's readiness for a planned amount of screen time after 11 pm tonight."""
    return forecast.train_and_forecast(_frame(), planned_screen_min=screen_min, exam_tomorrow=exam_tomorrow)


@app.get("/api/brief")
def brief():
    r = _result()
    return {"brief": r["brief"], "facts": r["facts"]}


@app.post("/api/brief/voice")
def brief_voice():
    path = voice.synthesize(_result()["brief"]["text"], config.STATE_DIR / "brief.mp3")
    if path is None:
        raise HTTPException(412, "Voice brief needs ELEVENLABS_API_KEY and 'voice_brief' consent")
    return FileResponse(path, media_type="audio/mpeg")


class ConsentChange(BaseModel):
    kind: str   # "sources" | "purposes"
    key: str
    value: bool


@app.get("/api/consent")
def get_consent():
    return consent.load()


@app.post("/api/consent")
def set_consent(change: ConsentChange):
    try:
        c = consent.update(change.kind, change.key, change.value)
    except KeyError as e:
        raise HTTPException(400, str(e)) from e
    return c


@app.get("/api/facts/{purpose}")
def released_facts(purpose: str):
    """What would leave the device for a given cloud purpose (403 without consent)."""
    try:
        return privacy.release(_result()["facts"], purpose)
    except privacy.ConsentError as e:
        raise HTTPException(403, str(e)) from e


app.mount("/static", StaticFiles(directory=ROOT / "dashboard"), name="static")


@app.get("/")
def dashboard():
    return FileResponse(ROOT / "dashboard" / "index.html")


try:  # AWS Lambda entry point (see infra/template.yaml)
    from mangum import Mangum
    handler = Mangum(app)
except ImportError:  # pragma: no cover
    handler = None
