"""Central configuration. Everything can be overridden with environment variables."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _load_dotenv(path: Path) -> None:
    """Minimal .env reader (KEY=VALUE lines). Real environment variables always win."""
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


_load_dotenv(ROOT / ".env")
DATA_DIR = Path(os.getenv("INTROSPECT_DATA_DIR", ROOT / "data" / "sample"))
STATE_DIR = Path(os.getenv("INTROSPECT_STATE_DIR", ROOT / ".introspect"))

# Personal baseline
BASELINE_WINDOW_DAYS = 28      # rolling window for "your normal"
MIN_BASELINE_DAYS = 7          # cold start: no personal alerts before this
ROBUST_Z_ALERT = 2.5           # |robust z| above this = drift worth flagging

# Why-engine
WHY_MIN_ABS_RHO = 0.30
WHY_MAX_P = 0.05

# Amazon Bedrock (optional; template narration is used when disabled)
USE_BEDROCK = os.getenv("INTROSPECT_USE_BEDROCK", "0") == "1"
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
BEDROCK_MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-3-haiku-20240307-v1:0")
BEDROCK_GUARDRAIL_ID = os.getenv("BEDROCK_GUARDRAIL_ID", "")
BEDROCK_GUARDRAIL_VERSION = os.getenv("BEDROCK_GUARDRAIL_VERSION", "DRAFT")

# ElevenLabs (optional)
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")
ELEVENLABS_MODEL_ID = os.getenv("ELEVENLABS_MODEL_ID", "eleven_multilingual_v2")
