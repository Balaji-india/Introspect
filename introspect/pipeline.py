"""End-to-end pipeline: ingest -> features -> baseline/anomaly -> why -> forecast -> facts -> brief."""
from __future__ import annotations

import math
from pathlib import Path

import pandas as pd

from . import baseline, config, features, forecast, ingest, narrate, privacy, why


def _r(x, nd=1):
    return None if x is None or (isinstance(x, float) and math.isnan(x)) else round(float(x), nd)


def build_frame(data_dir: str | Path | None = None, user_id: int | None = None) -> pd.DataFrame:
    """Ingest -> features -> personal baseline + anomaly flags."""
    df = ingest.build_timeline(data_dir or config.DATA_DIR, user_id)
    return baseline.compute_baseline(features.add_features(df))


def run(data_dir: str | Path | None = None, user_id: int | None = None,
        frame: pd.DataFrame | None = None, fitted: forecast.Fitted | dict | None = None) -> dict:
    """Full pipeline. `frame` / `fitted` let a caller (the API) reuse cached work."""
    df = frame if frame is not None else build_frame(data_dir, user_id)
    insights = why.as_dicts(why.find_insights(df))
    fc = forecast.predict(fitted if fitted is not None else forecast.fit(df))

    today = df.iloc[-1]
    last7 = df.tail(7)
    summary = {
        "period_days": int(len(df)),
        "readiness_7d_avg": _r(last7["readiness"].mean()),
        "sleep_7d_avg_min": _r(last7["sleep_min"].mean(), 0),
        "sleep_normal_min": _r(today.get("sleep_min_baseline"), 0),
        "resting_hr_7d_avg": _r(last7["resting_hr"].mean()) if "resting_hr" in df else None,
        "steps_7d_avg": _r(last7["steps"].mean(), 0),
        "is_exam_week": bool(last7.get("is_exam_day", pd.Series([0])).sum() >= 3),
    }
    # Latest day with a personal-baseline drift (what the brief talks about)
    day = {"date": today["date"].date().isoformat(), "readiness": _r(today["readiness"]),
           "drift": baseline.describe_drift(today)}
    facts = privacy.build_facts(day, insights, fc, summary)
    brief = narrate.daily_brief(facts)

    anomalies = df[df["is_anomaly"]].copy()
    timeline_cols = ["date", "sleep_min", "resting_hr", "hrv", "steps", "screen_after_11pm_min", "readiness",
                     "is_anomaly", "is_exam_day", "sleep_min_baseline"]
    tl = df[[c for c in timeline_cols if c in df]].copy()
    tl["date"] = tl["date"].dt.strftime("%Y-%m-%d")
    return {
        "timeline": tl.astype(object).where(tl.notna(), None).to_dict(orient="records"),
        "anomalies": [{"date": r["date"].date().isoformat(), "drift": baseline.describe_drift(r),
                       "iforest_score": _r(r["iforest_score"], 3)} for _, r in anomalies.iterrows()],
        "insights": insights,
        "forecast": fc,
        "facts": facts,
        "brief": brief,
    }
