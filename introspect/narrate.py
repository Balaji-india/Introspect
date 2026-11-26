"""Turns facts into a short daily brief.

Default: deterministic template (works offline, zero cost).
Optional: Amazon Bedrock (Claude Haiku) with Bedrock Guardrails. The model only gets the
privacy-gateway facts, and its output is rejected if it contains numbers that are not in the
facts, so it cannot invent statistics. Any failure falls back to the template.
"""
from __future__ import annotations

import json
import re

from . import config, privacy

SYSTEM = ("You are Introspect, a calm personal wellness coach. Write a 60-second spoken daily brief "
          "(max 90 words) using ONLY the facts given. Do not add numbers that are not in the facts. "
          "Do not diagnose or mention diseases. End with exactly one suggested action.")


def template_brief(f: dict) -> str:
    parts = []
    r, avg = f.get("readiness_today"), f.get("readiness_7d_avg")
    if r is not None:
        mood = "above" if r > 55 else "below" if r < 45 else "close to"
        parts.append(f"Good morning. Your readiness today is {r:.0f}, {mood} your normal.")
    for d in f.get("drift_today", []):
        parts.append(f"Your {d['metric']} was {d['value']:g} {d['unit']}, against a normal of {d['your_normal']:g}.")
    if f.get("is_exam_week") and f.get("sleep_7d_avg_min") is not None and f.get("sleep_normal_min") is not None:
        parts.append(f"Your calendar shows an exam week: you averaged {f['sleep_7d_avg_min']:.0f} min of sleep "
                     f"over the last 7 days, against a normal of {f['sleep_normal_min']:.0f}.")
    if f.get("insights"):
        parts.append(f["insights"][0])
    if f.get("readiness_forecast_tomorrow") is not None:
        parts.append(f"With a usual night, tomorrow's readiness looks like about {f['readiness_forecast_tomorrow']:.0f}.")
    parts.append(f["suggested_action"])
    return " ".join(parts)


def _numbers(text: str) -> set[str]:
    return {n.rstrip(".0") or "0" for n in re.findall(r"\d+(?:\.\d+)?", text)}


def grounded(text: str, facts: dict) -> bool:
    """Every number in the LLM text must appear in the facts (after rounding)."""
    allowed = set()
    for n in re.findall(r"\d+(?:\.\d+)?", json.dumps(facts)):
        v = float(n)
        allowed |= {str(round(v)), f"{v:g}", n}
    return all(n in allowed or n.rstrip(".0") in allowed for n in re.findall(r"\d+(?:\.\d+)?", text))


def bedrock_converse(system: str, user_text: str, max_tokens: int = 220) -> str:
    """One Bedrock Converse call (Claude Haiku), with Guardrails when configured."""
    import boto3  # imported lazily so the offline demo has no AWS dependency at runtime

    client = boto3.client("bedrock-runtime", region_name=config.AWS_REGION)
    kwargs = dict(
        modelId=config.BEDROCK_MODEL_ID,
        system=[{"text": system}],
        messages=[{"role": "user", "content": [{"text": user_text}]}],
        inferenceConfig={"maxTokens": max_tokens, "temperature": 0.3},
    )
    if config.BEDROCK_GUARDRAIL_ID:
        kwargs["guardrailConfig"] = {"guardrailIdentifier": config.BEDROCK_GUARDRAIL_ID,
                                     "guardrailVersion": config.BEDROCK_GUARDRAIL_VERSION}
    resp = client.converse(**kwargs)
    return resp["output"]["message"]["content"][0]["text"].strip()


def bedrock_brief(facts: dict) -> str:
    facts = privacy.release(facts, "cloud_narration")
    return bedrock_converse(SYSTEM, "Facts:\n" + json.dumps(facts))


def daily_brief(facts: dict) -> dict:
    if config.USE_BEDROCK:
        try:
            text = bedrock_brief(facts)
            if grounded(text, facts):
                return {"text": text, "source": "bedrock", "model": config.BEDROCK_MODEL_ID}
            return {"text": template_brief(facts), "source": "template",
                    "note": "Bedrock output contained ungrounded numbers; fell back to template"}
        except Exception as e:  # noqa: BLE001 - never let the brief fail
            return {"text": template_brief(facts), "source": "template", "note": f"Bedrock unavailable: {e}"}
    return {"text": template_brief(facts), "source": "template"}
