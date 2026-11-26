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
