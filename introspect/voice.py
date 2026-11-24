"""ElevenLabs voice brief (optional). Needs ELEVENLABS_API_KEY and 'voice_brief' consent."""
from __future__ import annotations

from pathlib import Path

import requests

from . import config, consent

API = "https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"


def synthesize(text: str, out_path: str | Path) -> Path | None:
    if not config.ELEVENLABS_API_KEY or not consent.allowed("voice_brief"):
        return None
    r = requests.post(
        API.format(voice_id=config.ELEVENLABS_VOICE_ID),
        headers={"xi-api-key": config.ELEVENLABS_API_KEY, "accept": "audio/mpeg"},
        json={"text": text, "model_id": config.ELEVENLABS_MODEL_ID,
              "voice_settings": {"stability": 0.5, "similarity_boost": 0.75}},
        timeout=60,
    )
    r.raise_for_status()
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(r.content)
    return out
