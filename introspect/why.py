"""Why-engine: finds the most likely driver behind a metric, in plain language.

Approach (deliberately simple + explainable):
  * Spearman correlation between candidate drivers and outcomes, with the right lag
    (e.g. screen time tonight -> sleep tonight; short sleep last night -> RHR today).
  * Effect size = difference in the outcome between the driver's top and bottom thirds.
  * Only report if |rho| >= 0.30 and p < 0.05; correlation is labelled as such.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict

import pandas as pd
from scipy.stats import spearmanr

from . import config

# (driver column, outcome column, human description of driver, human outcome, unit)
CANDIDATES = [
    ("screen_after_11pm_min", "sleep_min", "screen time after 11 pm", "sleep", "min"),
    ("sleep_min_lag1", "resting_hr", "short sleep the night before", "resting heart rate", "bpm"),
    ("sleep_min_lag1", "hrv", "short sleep the night before", "HRV", "ms"),
    ("is_exam_day", "sleep_min", "exam days", "sleep", "min"),
    ("events", "sleep_min", "busy calendar days", "sleep", "min"),
    ("steps", "sleep_min", "more daily steps", "sleep", "min"),
    ("screen_after_11pm_min", "readiness", "screen time after 11 pm", "next-day readiness", "pts"),
]


ACTIONABLE = {"screen_after_11pm_min", "steps", "events"}


@dataclass
class Insight:
    driver: str
    outcome: str
    rho: float
    p_value: float
    n_days: int
    effect: float          # outcome(high driver) - outcome(low driver)
    unit: str
    high_threshold: float  # what "high driver" means for this person
    sentence: str


def _sentence(desc, outcome, effect, unit, thr, driver_col):
    more_less = "less" if effect < 0 else "more"
    mag = abs(round(effect)) if unit in ("min", "pts") else abs(round(effect, 1))
    if driver_col == "is_exam_day":
        cond = "On exam days"
    elif driver_col.startswith("sleep_min"):
        cond = "After your shorter nights"
        if outcome == "resting heart rate":
            return f"{cond}, your resting heart rate runs about {mag} bpm {'higher' if effect > 0 else 'lower'}."
        if outcome == "HRV":
            return f"{cond}, your HRV is about {mag} ms {'higher' if effect > 0 else 'lower'}."
    else:
        cond = f"On days with {desc} above ~{int(thr)}" + (" min" if "min" in driver_col else "")
    if unit == "pts":
        return f"{cond}, your next-day readiness is about {mag} points {'lower' if effect < 0 else 'higher'}."
    return f"{cond}, you get about {mag} {unit} {more_less} {outcome}."


def find_insights(df: pd.DataFrame, top_k: int = 3) -> list[Insight]:
    work = df.copy()
    if "readiness" in work:
        work["readiness"] = work["readiness"].shift(-1)   # tonight's behaviour -> tomorrow's readiness
    found = []
    for drv, out, desc, outcome, unit in CANDIDATES:
        if drv not in work or out not in work:
            continue
        pair = work[[drv, out]].dropna()
        if len(pair) < 14 or pair[drv].nunique() < 2:
            continue
        rho, p = spearmanr(pair[drv], pair[out])
        if abs(rho) < config.WHY_MIN_ABS_RHO or p > config.WHY_MAX_P:
            continue
        if pair[drv].nunique() == 2:
            hi_mask, lo_mask, thr = pair[drv] == pair[drv].max(), pair[drv] == pair[drv].min(), 1
        else:
            lo_q, hi_q = pair[drv].quantile([1 / 3, 2 / 3])
            hi_mask, lo_mask, thr = pair[drv] >= hi_q, pair[drv] <= lo_q, hi_q
        effect = pair.loc[hi_mask, out].mean() - pair.loc[lo_mask, out].mean()
        if drv.startswith("sleep_min"):
            effect = -effect          # phrase as "after SHORTER nights"
        found.append(Insight(drv, outcome, round(float(rho), 2), float(p), len(pair), round(float(effect), 1),
                             unit, round(float(thr), 1), _sentence(desc, outcome, effect, unit, thr, drv)))
    # Things you can change (screen time, steps) come before physiology, then by strength
    found.sort(key=lambda i: (i.driver not in ACTIONABLE, -abs(i.rho)))
    # keep one insight per outcome, strongest first
    seen, out = set(), []
    for ins in found:
        if ins.outcome not in seen:
            seen.add(ins.outcome)
            out.append(ins)
    return out[:top_k]


def as_dicts(insights: list[Insight]) -> list[dict]:
    return [{**asdict(i), "p_value": float(f"{i.p_value:.2g}")} for i in insights]
