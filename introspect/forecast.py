"""Tomorrow's readiness forecast with a "what-if" on tonight's plan (LightGBM).

Features are what you know *today*: today's readiness, recent sleep debt and activity,
plus tonight's plan (screen time after 11 pm) and tomorrow's calendar (exam? how busy?).
That lets the app answer: "if you stop screens at 11, tomorrow looks like X instead of Y".

The model learns a correction on top of "tomorrow = today" (persistence). It is evaluated
with a time-ordered split against persistence and the personal mean. With ~2 months of data it
is roughly on par with persistence; the value today is the monotonic what-if, and accuracy is
the main thing we will validate on real data (see README).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

try:
    from lightgbm import LGBMRegressor
except ImportError:  # pragma: no cover
    LGBMRegressor = None
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error

FEATURES = ["readiness", "sleep_debt_3d", "steps_7d", "planned_screen_min", "exam_tomorrow",
            "events_tomorrow", "weekend_tomorrow"]
# Domain knowledge as monotonic constraints (stops small-data nonsense like
# "more late-night screen time -> better tomorrow"): +1 increasing, -1 decreasing, 0 free
# The model predicts the CHANGE from today's readiness (persistence + learned correction),
# so `readiness` itself is left unconstrained.
MONOTONE = [0, -1, 0, -1, -1, -1, 0]


def _model():
    if LGBMRegressor is not None:
        return LGBMRegressor(n_estimators=120, learning_rate=0.05, num_leaves=5, min_child_samples=5,
                             monotone_constraints=MONOTONE, random_state=0, verbose=-1)
    return HistGradientBoostingRegressor(max_depth=3, monotonic_cst=MONOTONE, random_state=0)


def design_matrix(df: pd.DataFrame) -> pd.DataFrame:
    X = pd.DataFrame(index=df.index)
    X["readiness"] = df["readiness"]
    X["sleep_debt_3d"] = df.get("sleep_debt_3d")
    X["steps_7d"] = df.get("steps_7d")
    X["planned_screen_min"] = df.get("screen_after_11pm_min", pd.Series(np.nan, index=df.index)).shift(-1)
    X["exam_tomorrow"] = df.get("is_exam_day", pd.Series(0, index=df.index)).shift(-1)
    X["events_tomorrow"] = df.get("events", pd.Series(np.nan, index=df.index)).shift(-1)
    X["weekend_tomorrow"] = df["is_weekend"].shift(-1)
    X["target"] = df["readiness"].shift(-1)
    return X


def train_and_forecast(df: pd.DataFrame, planned_screen_min: float | None = None,
                       exam_tomorrow: int = 0, events_tomorrow: float | None = None) -> dict:
    X = design_matrix(df)
    train = X.dropna()
    if len(train) < 20:
        return {"status": "need more days", "days_available": int(len(train))}
    split = int(len(train) * 0.7)
    tr, te = train.iloc[:split], train.iloc[split:]
    m = _model().fit(tr[FEATURES], tr["target"] - tr["readiness"])
    mae = mean_absolute_error(te["target"], te["readiness"] + m.predict(te[FEATURES]))
    persist = mean_absolute_error(te["target"], te["readiness"])
    mean_b = mean_absolute_error(te["target"], np.full(len(te), tr["target"].mean()))
    model = _model().fit(train[FEATURES], train["target"] - train["readiness"])

    today = df.iloc[-1]
    usual_screen = float(df["screen_after_11pm_min"].median()) if "screen_after_11pm_min" in df else 0.0
    usual_events = float(df["events"].median()) if "events" in df else 0.0

    def predict(screen):
        row = pd.DataFrame([{
            "readiness": today["readiness"], "sleep_debt_3d": today.get("sleep_debt_3d", 0),
            "steps_7d": today.get("steps_7d", np.nan), "planned_screen_min": screen,
            "exam_tomorrow": exam_tomorrow, "events_tomorrow": usual_events if events_tomorrow is None else events_tomorrow,
            "weekend_tomorrow": int((today["date"] + pd.Timedelta(days=1)).dayofweek >= 5),
        }])[FEATURES]
        return round(float(np.clip(today["readiness"] + model.predict(row)[0], 0, 100)), 1)

    screen = usual_screen if planned_screen_min is None else planned_screen_min
    return {"status": "ok", "tomorrow_readiness": predict(screen), "planned_screen_min": round(screen),
            "what_if": {"screens_off_by_11pm": predict(10), "usual_night": predict(usual_screen),
                        "late_night_2h": predict(120)},
            "eval": {"test_mae": round(float(mae), 1), "persistence_mae": round(float(persist), 1),
                     "personal_mean_mae": round(float(mean_b), 1), "train_days": int(split),
                     "test_days": int(len(te))},
            "model": type(model).__name__}
