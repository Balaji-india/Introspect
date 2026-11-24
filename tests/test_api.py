import sys
from pathlib import Path

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from api.main import app  # noqa: E402

client = TestClient(app)


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
