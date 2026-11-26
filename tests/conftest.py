"""Tests never use real cloud services, even if a developer's .env enables them."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from introspect import config  # noqa: E402


@pytest.fixture(autouse=True)
def offline_by_default(monkeypatch):
    monkeypatch.setattr(config, "USE_BEDROCK", False)
    monkeypatch.setattr(config, "ELEVENLABS_API_KEY", "")
