"""Privacy gateway: the ONLY thing allowed to hand data to the cloud.

Rules enforced here:
  * no user ids, no raw time series, no exact dates -> only rounded aggregates + insights
  * consent is checked per purpose before anything leaves the device
  * an allow-list of keys; anything else raises
"""
from __future__ import annotations

from . import consent

ALLOWED_KEYS = {"period_days", "readiness_today", "readiness_7d_avg", "readiness_forecast_tomorrow",
                "drift_today", "insights", "sleep_7d_avg_min", "sleep_normal_min", "resting_hr_7d_avg",
                "steps_7d_avg", "is_exam_week", "suggested_action"}


class ConsentError(PermissionError):
    pass


def build_facts(day: dict, insights: list[dict], forecast: dict, summary: dict) -> dict:
    """Aggregate, de-identified facts about the user. Safe to show anyone the user chooses."""
    facts = {
        "period_days": summary["period_days"],
        "readiness_today": day.get("readiness"),
        "readiness_7d_avg": summary["readiness_7d_avg"],
        "readiness_forecast_tomorrow": forecast.get("tomorrow_readiness"),
        "drift_today": day.get("drift", []),
        "insights": [i["sentence"] for i in insights],
        "sleep_7d_avg_min": summary["sleep_7d_avg_min"],
        "sleep_normal_min": summary["sleep_normal_min"],
        "resting_hr_7d_avg": summary["resting_hr_7d_avg"],
        "steps_7d_avg": summary["steps_7d_avg"],
        "is_exam_week": summary["is_exam_week"],
        "suggested_action": suggest_action(day, insights),
    }
    check(facts)
    return facts


def check(facts: dict) -> None:
    extra = set(facts) - ALLOWED_KEYS
    if extra:
        raise ValueError(f"privacy gateway blocked non-aggregate keys: {sorted(extra)}")


def release(facts: dict, purpose: str) -> dict:
    """Return facts for a cloud purpose only if the user consented to it."""
    if not consent.allowed(purpose):
        raise ConsentError(f"user has not consented to '{purpose}'")
    check(facts)
    return facts


def suggest_action(day: dict, insights: list[dict]) -> str:
    drift = {d["metric"] for d in day.get("drift", [])}
    if {"resting heart rate", "HRV"} & drift and "sleep" in drift:
        return "Take it easy today: keep training light and aim for bed 45 minutes earlier."
    for i in insights:
        if i["driver"] == "screen_after_11pm_min":
            return "Tonight, put the phone away by 11 pm. It is your biggest lever for sleep."
    if "steps" in drift:
        return "Fit in a 20-minute walk today; your activity is well below your normal."
    return "You are close to your normal. Keep your usual sleep window tonight."
