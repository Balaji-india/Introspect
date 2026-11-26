"""Introspect API (FastAPI). Runs locally, or on AWS Lambda behind API Gateway via Mangum.

    uvicorn api.main:app --reload        # then open http://127.0.0.1:8000
"""
from __future__ import annotations

import shutil
from functools import lru_cache
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from introspect import __version__, config, consent, forecast, pipeline, privacy, synthetic, voice

ROOT = Path(__file__).resolve().parent.parent
app = FastAPI(title="Introspect API", version=__version__,
              description="Private personal-intelligence twin: baseline, anomalies, why-engine, forecast, brief.")


# --- active dataset + caches -------------------------------------------------------------
# All endpoints read the *active* dataset (default: config.DATA_DIR). Demo scenarios switch it.
_active: dict[str, Path | None] = {"dir": None}


def data_dir() -> Path:
    return Path(_active["dir"] or config.DATA_DIR)


@lru_cache(maxsize=8)
def _frame_for(d: str):
    return pipeline.build_frame(d)


@lru_cache(maxsize=8)
def _fitted_for(d: str):
    return forecast.fit(_frame_for(d))          # trained once per dataset; the slider only predicts


@lru_cache(maxsize=8)
def _result_for(d: str):
    return pipeline.run(d, frame=_frame_for(d), fitted=_fitted_for(d))


def _result():
    return _result_for(str(data_dir()))


def _fitted():
    return _fitted_for(str(data_dir()))


def clear_caches() -> None:
    for f in (_frame_for, _fitted_for, _result_for):
        f.cache_clear()


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
    return forecast.predict(_fitted(), planned_screen_min=screen_min, exam_tomorrow=exam_tomorrow)


@app.get("/api/brief")
def brief():
    r = _result()
    return {"brief": r["brief"], "facts": r["facts"]}


@app.post("/api/brief/voice")
def brief_voice():
    try:
        path = voice.synthesize(_result()["brief"]["text"], config.STATE_DIR / "brief.mp3")
    except Exception as e:  # noqa: BLE001 - network/API errors: the dashboard falls back to the device voice
        raise HTTPException(502, f"ElevenLabs unavailable ({type(e).__name__}); using device voice") from e
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


# --- demo controls ------------------------------------------------------------------------
# Only these paths inside STATE_DIR are ever deleted by a reset (never the whole folder).
_STATE_FILES = ("consent.json", "brief.mp3")
_STATE_DIRS = ("demo_data", "upload")


@app.post("/api/demo/reset")
def demo_reset():
    """Back to the first-load state: default consent, default sample data, empty caches."""
    for name in _STATE_FILES:
        (config.STATE_DIR / name).unlink(missing_ok=True)
    for name in _STATE_DIRS:
        shutil.rmtree(config.STATE_DIR / name, ignore_errors=True)
    _active["dir"] = None
    clear_caches()
    _result()                                   # rebuild now so the reloaded page is instant
    return {"status": "ok", "dataset": "sample", "consent": consent.load()}


class ScenarioChange(BaseModel):
    scenario: str   # one of synthetic.SCENARIOS


@app.get("/api/demo/scenario")
def get_scenario():
    d = _active["dir"]
    return {"scenario": Path(d).name if d else "default", "available": list(synthetic.SCENARIOS)}


@app.post("/api/demo/scenario")
def set_scenario(change: ScenarioChange):
    """Swap in a synthetic scenario (normal / exam_week / bad_night) and recompute everything."""
    if change.scenario not in synthetic.SCENARIOS:
        raise HTTPException(400, f"unknown scenario; choose from {list(synthetic.SCENARIOS)}")
    if change.scenario == "default":
        _active["dir"] = None
    else:
        _active["dir"] = synthetic.generate(config.STATE_DIR / "demo_data" / change.scenario, scenario=change.scenario)
    clear_caches()
    _result()                                   # recompute now so the dashboard re-fetch is instant
    return get_scenario()


app.mount("/static", StaticFiles(directory=ROOT / "dashboard"), name="static")


@app.get("/")
def dashboard():
    return FileResponse(ROOT / "dashboard" / "index.html")


try:  # AWS Lambda entry point (see infra/template.yaml)
    from mangum import Mangum
    handler = Mangum(app)
except ImportError:  # pragma: no cover
    handler = None
