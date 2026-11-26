import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from api import main  # noqa: E402
from api.main import app  # noqa: E402
from introspect import config  # noqa: E402

client = TestClient(app)


@pytest.fixture(autouse=True)
def isolated_state(tmp_path, monkeypatch):
    """Never touch the real .introspect/ folder; start every test from the default dataset."""
    monkeypatch.setattr(config, "STATE_DIR", tmp_path / "state")
    main._active["dir"] = None
    yield
    main._active["dir"] = None


def test_endpoints():
    assert client.get("/api/health").json()["status"] == "ok"
    assert len(client.get("/api/timeline").json()) == 60
    assert client.get("/api/insights").json()
    assert "text" in client.get("/api/brief").json()["brief"]
    f = client.get("/api/forecast", params={"screen_min": 0}).json()
    assert f["status"] == "ok"
    assert client.get("/").status_code == 200
    assert client.get("/static/vendor/chart.umd.min.js").status_code == 200


def test_voice_requires_key_and_consent():
    assert client.post("/api/brief/voice").status_code == 412


def test_what_if_slider_is_fast_after_first_call():
    import time

    client.get("/api/forecast")                       # first call trains + caches
    t0 = time.perf_counter()
    values = [client.get("/api/forecast", params={"screen_min": s}).json()["tomorrow_readiness"]
              for s in range(0, 190, 10)]
    per_call_ms = (time.perf_counter() - t0) * 1000 / len(values)
    assert per_call_ms < 150
    assert values == sorted(values, reverse=True)     # monotonic: more late screen never helps


def test_demo_reset_restores_first_load_state():
    first = client.get("/api/brief").json()
    client.post("/api/consent", json={"kind": "purposes", "key": "cloud_narration", "value": True})
    (config.STATE_DIR / "demo_data").mkdir(parents=True)
    keep = config.STATE_DIR / "notes.txt"
    keep.write_text("not ours")
    assert client.get("/api/consent").json()["purposes"]["cloud_narration"] is True

    r = client.post("/api/demo/reset").json()
    assert r["status"] == "ok"
    assert client.get("/api/consent").json()["purposes"]["cloud_narration"] is False
    assert not (config.STATE_DIR / "demo_data").exists()
    assert keep.exists()                                # reset only deletes its own files
    assert client.get("/api/brief").json() == first


def test_scenario_switch_updates_every_endpoint():
    before = client.get("/api/timeline").json()
    r = client.post("/api/demo/scenario", json={"scenario": "bad_night"})
    assert r.status_code == 200 and r.json()["scenario"] == "bad_night"
    assert (config.STATE_DIR / "demo_data" / "bad_night" / "dailyActivity_merged.csv").exists()
    after = client.get("/api/timeline").json()
    assert after[-1]["is_anomaly"] and not before[-1]["is_anomaly"]
    assert "Take it easy" in client.get("/api/brief").json()["brief"]["text"]
    assert client.get("/api/forecast", params={"screen_min": 30}).json()["status"] == "ok"
    assert client.post("/api/demo/scenario", json={"scenario": "nope"}).status_code == 400
    client.post("/api/demo/reset")
    assert client.get("/api/demo/scenario").json()["scenario"] == "default"
    assert client.get("/api/timeline").json() == before


def test_privacy_card_flips_with_consent():
    assert "What leaves this device" in client.get("/").text
    assert client.get("/api/facts/cloud_narration").status_code == 403
    client.post("/api/consent", json={"kind": "purposes", "key": "cloud_narration", "value": True})
    facts = client.get("/api/facts/cloud_narration").json()
    assert "readiness_today" in facts and "insights" in facts
    text = str(facts)
    assert "2026-" not in text and "1503960366" not in text      # no dates, no ids
    assert not any(isinstance(v, list) and v and isinstance(v[0], (int, float)) for v in facts.values())
    client.post("/api/consent", json={"kind": "purposes", "key": "cloud_narration", "value": False})
    assert client.get("/api/facts/cloud_narration").status_code == 403


def test_voice_uses_elevenlabs_with_key_and_consent_else_signals_fallback(monkeypatch):
    import requests

    assert "device voice" in client.get("/").text                    # button label advertises the fallback
    monkeypatch.setattr(config, "ELEVENLABS_API_KEY", "test-key")
    assert client.post("/api/brief/voice").status_code == 412        # key but no consent
    client.post("/api/consent", json={"kind": "purposes", "key": "voice_brief", "value": True})

    class Resp:
        content = b"ID3fake-mp3"

        def raise_for_status(self):
            pass

    monkeypatch.setattr(requests, "post", lambda *a, **k: Resp())
    r = client.post("/api/brief/voice")
    assert r.status_code == 200 and r.headers["content-type"] == "audio/mpeg" and r.content == Resp.content

    def offline(*a, **k):
        raise requests.ConnectionError("no internet")

    monkeypatch.setattr(requests, "post", offline)
    r = client.post("/api/brief/voice")
    assert r.status_code == 502 and "test-key" not in r.text           # never leak the key
