"""Ask your data: answers questions using ONLY the privacy-gateway facts.

On-device (default): a deterministic intent matcher. Every number in an answer comes straight
from the facts, so answers pass the same grounding check as the Bedrock brief.
Cloud (optional): if Bedrock is enabled AND the user consented to 'cloud_narration', the question
plus the facts go to Bedrock with the narrator's rules; the answer is kept only if every number in it
is grounded in the facts. Anything else falls back to the on-device answer.
"""
from __future__ import annotations

import json
import re

from . import config, consent, narrate, privacy

ASK_SYSTEM = ("You are Introspect, a calm personal wellness coach. Answer the user's question in at most 60 words "
              "using ONLY the facts given. Do not add numbers that are not in the facts. Do not diagnose or mention "
              "diseases. If the facts cannot answer the question, say so briefly.")

# Checked in order; the first intent with a matching keyword wins.
INTENTS = [
    ("tomorrow", ("tomorrow", "forecast", "predict", "next day", "will i")),
    ("change", ("change", "should i", "improve", "tip", "advice", "what can i do", "fix", "better")),
    ("why", ("why", "tired", "exhausted", "drained", "fatigue", "sleepy", "low energy", "cause")),
    ("sleep", ("sleep", "slept", "bed", "night")),
    ("steps", ("step", "walk", "activity", "active", "exercise", "move")),
    ("readiness", ("readiness", "ready", "recovery", "recovered", "how am i", "today", "feel")),
    ("help", ("help", "what can you", "hello", "hi")),
]

HELP = ("I answer from your on-device insights. Try \"Why am I tired?\", \"How will tomorrow be?\", "
        "\"What should I change?\", \"How did I sleep?\" or \"How active was I?\"")


def intent(question: str) -> str:
    q = " " + re.sub(r"[^a-z ]+", " ", question.lower()) + " "
    for name, words in INTENTS:
        if any(f" {w}" in q for w in words):
            return name
    return "help"


def _n(x) -> str:
    return f"{x:.0f}"


def _where(r: float) -> str:
    return "above" if r > 55 else "below" if r < 45 else "close to"


def _readiness(f: dict) -> str:
    r = f.get("readiness_today")
    if r is None:
        return "I don't have a readiness score for today yet."
    return f"Your readiness today is {_n(r)}, {_where(r)} your normal (7-day average {_n(f['readiness_7d_avg'])})."


def _sleep(f: dict) -> str:
    avg, normal = f.get("sleep_7d_avg_min"), f.get("sleep_normal_min")
    if avg is None or normal is None:
        return "I don't have enough sleep data yet."
    diff = avg - normal
    cmp = "about your normal" if abs(diff) < 10 else ("less than" if diff < 0 else "more than") + " your normal"
    return f"Over the last 7 days you averaged {_n(avg)} min of sleep a night, {cmp} of {_n(normal)} min."


def _drift(f: dict) -> str:
    d = f.get("drift_today") or []
    if not d:
        return ""
    parts = [f"{x['metric']} {x['value']:g} {x['unit']} vs your normal {x['your_normal']:g}" for x in d]
    return "Today drifted from your baseline: " + "; ".join(parts) + "."


def on_device_answer(question: str, f: dict) -> tuple[str, str]:
    kind = intent(question)
    insights = f.get("insights") or []
    top = insights[0] if insights else ""
    if kind == "why":
        parts = [_drift(f) or _readiness(f), _sleep(f)]
        if top:
            parts.append(f"The strongest pattern in your data: {top}")
        if f.get("is_exam_week"):
            parts.append("Your calendar also shows an exam week.")
        parts.append("These are patterns in your own data, not a diagnosis.")
    elif kind == "tomorrow":
        t = f.get("readiness_forecast_tomorrow")
        parts = [f"With a usual night, tomorrow's readiness looks like about {_n(t)}, {_where(t)} your normal."
                 if t is not None else "I need a few more days of data before I can forecast tomorrow."]
        parts.append("Tonight's late-night screen time is the lever you control; try the what-if slider.")
    elif kind == "change":
        parts = [f["suggested_action"]]
        if top:
            parts.append(f"Why: {top}")
    elif kind == "sleep":
        parts = [_sleep(f)] + ([top] if top and "sleep" in top else [])
    elif kind == "steps":
        s = f.get("steps_7d_avg")
        parts = [f"You averaged {_n(s)} steps a day over the last 7 days." if s is not None
                 else "I don't have step data yet."]
    elif kind == "readiness":
        parts = [_readiness(f), _drift(f)]
    else:
        parts = [HELP]
    return " ".join(p for p in parts if p), kind


def answer(question: str, facts: dict) -> dict:
    question = (question or "").strip()[:300]
    text, kind = on_device_answer(question, facts)
    if config.USE_BEDROCK and consent.allowed("cloud_narration") and question:
        try:
            released = privacy.release(facts, "cloud_narration")
            llm = narrate.bedrock_converse(ASK_SYSTEM, f"Facts:\n{json.dumps(released)}\n\nQuestion: {question}", 160)
            if narrate.grounded(llm, released):
                return {"answer": llm, "source": "bedrock", "intent": kind}
            return {"answer": text, "source": "on-device", "intent": kind,
                    "note": "Bedrock answer had ungrounded numbers; used the on-device answer"}
        except Exception as e:  # noqa: BLE001 - never let Ask fail
            return {"answer": text, "source": "on-device", "intent": kind,
                    "note": f"Bedrock unavailable: {type(e).__name__}"}
    return {"answer": text, "source": "on-device", "intent": kind}
