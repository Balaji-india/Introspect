"""Personal baseline ("your normal") + anomaly detection.

Two complementary detectors:
  1. Per-metric robust z-score against YOUR rolling 28-day median/MAD (explainable,
     works from day 7, ignores population averages).
  2. Multivariate Isolation Forest over the day's standardised metrics, which catches
     unusual *combinations* (e.g. normal sleep but high RHR and low HRV together).
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

from . import config
from .features import CORE_METRICS

# +1 = higher is better, -1 = lower is better
DIRECTION = {"sleep_min": 1, "hrv": 1, "steps": 1, "resting_hr": -1}
LABEL = {"sleep_min": "sleep", "resting_hr": "resting heart rate", "hrv": "HRV", "steps": "steps"}
UNIT = {"sleep_min": "min", "resting_hr": "bpm", "hrv": "ms", "steps": "steps"}


def robust_z(series: pd.Series, window: int = config.BASELINE_WINDOW_DAYS,
             min_days: int = config.MIN_BASELINE_DAYS) -> tuple[pd.Series, pd.Series]:
    """z of each day vs the PREVIOUS `window` days (today never leaks into its own baseline).

    Centre = rolling median, spread = rolling IQR / 1.349 (a robust sigma estimate), so one
    bad night does not drag "your normal" around.
    """
    hist = series.astype(float).shift(1).rolling(window, min_periods=min_days)
    med = hist.median()
    scale = ((hist.quantile(0.75) - hist.quantile(0.25)) / 1.349).replace(0, np.nan)
    return (series - med) / scale, med


def compute_baseline(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for m in CORE_METRICS:
        if m in df:
            z, med = robust_z(df[m])
            df[f"{m}_z"] = z
            df[f"{m}_baseline"] = med
    df["readiness"] = readiness_score(df)
    df["iforest_score"], df["iforest_anomaly"] = isolation_forest(df)
    flags = []
    for _, row in df.iterrows():
        f = [m for m in CORE_METRICS if f"{m}_z" in row and pd.notna(row[f"{m}_z"])
             and abs(row[f"{m}_z"]) >= config.ROBUST_Z_ALERT and np.sign(row[f"{m}_z"]) == -DIRECTION[m]]
        flags.append(f)
    df["drift_metrics"] = flags
    df["is_anomaly"] = df["drift_metrics"].map(bool) | df["iforest_anomaly"]
    return df


def readiness_score(df: pd.DataFrame) -> pd.Series:
    """0-100 recovery score from personal z-scores (50 = your normal)."""
    parts = []
    for m, w in (("sleep_min", 0.4), ("hrv", 0.35), ("resting_hr", 0.25)):
        if f"{m}_z" in df:
            parts.append(w * DIRECTION[m] * df[f"{m}_z"].clip(-3, 3))
    if not parts:
        return pd.Series(np.nan, index=df.index)
    s = sum(parts)
    return (50 + s * 16).clip(0, 100).round(1)


def isolation_forest(df: pd.DataFrame, contamination: float = 0.05):
    cols = [f"{m}_z" for m in CORE_METRICS if f"{m}_z" in df]
    X = df[cols]
    ok = X.notna().all(axis=1)
    score = pd.Series(np.nan, index=df.index)
    flag = pd.Series(False, index=df.index)
    if ok.sum() < 14:
        return score, flag
    model = IsolationForest(n_estimators=200, contamination=contamination, random_state=0)
    model.fit(X[ok])
    score[ok] = -model.score_samples(X[ok])        # higher = more unusual
    flag[ok] = model.predict(X[ok]) == -1
    return score.round(3), flag


def describe_drift(row: pd.Series) -> list[dict]:
    """Human-readable drift facts for one day (consumed by the privacy gateway + narrator)."""
    out = []
    for m in row.get("drift_metrics", []):
        base, val = row[f"{m}_baseline"], row[m]
        out.append({"metric": LABEL[m], "value": round(float(val), 1), "your_normal": round(float(base), 1),
                    "unit": UNIT[m], "robust_z": round(float(row[f"{m}_z"]), 2)})
    return out
