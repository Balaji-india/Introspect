"""Consent vault: per-source and per-purpose consent, stored locally (DPDP-style).

Locally this is a JSON file; in the cloud the same records go to a DynamoDB
"consent ledger" table (see infra/template.yaml) so every change is auditable.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone

from . import config

DEFAULT = {
    "sources": {"wearable": True, "screen_time": True, "calendar": True, "checkins": True},
    "purposes": {"cloud_narration": False, "voice_brief": False, "mcp_access": False, "cloud_backup": False},
}


def _path():
    config.STATE_DIR.mkdir(parents=True, exist_ok=True)
    return config.STATE_DIR / "consent.json"


def load() -> dict:
    p = _path()
    if p.exists():
        return json.loads(p.read_text())
    return json.loads(json.dumps(DEFAULT))


def update(kind: str, key: str, value: bool) -> dict:
    c = load()
    if kind not in c or key not in c[kind]:
        raise KeyError(f"unknown consent {kind}.{key}")
    c[kind][key] = bool(value)
    c.setdefault("log", []).append({"at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                                    "kind": kind, "key": key, "value": bool(value)})
    _path().write_text(json.dumps(c, indent=2))
    return c


def allowed(purpose: str) -> bool:
    return bool(load()["purposes"].get(purpose, False))
