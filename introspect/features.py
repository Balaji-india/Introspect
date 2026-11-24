"""Daily feature engineering: rolling context and lags used by the models."""
from __future__ import annotations

import pandas as pd

CORE_METRICS = ["sleep_min", "resting_hr", "hrv", "steps"]


def add_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy().sort_values("date").reset_index(drop=True)
    df["weekday"] = df["date"].dt.dayofweek
    df["is_weekend"] = (df["weekday"] >= 5).astype(int)
    if "sleep_min" in df:
        df["sleep_eff"] = (df["sleep_min"] / df["in_bed_min"]).clip(0, 1) if "in_bed_min" in df else None
        df["sleep_debt_3d"] = (df["sleep_min"].rolling(7, min_periods=3).median()
                               - df["sleep_min"]).rolling(3, min_periods=1).sum()
    for col in ("sleep_min", "steps", "screen_after_11pm_min"):
        if col in df:
            df[f"{col}_lag1"] = df[col].shift(1)
    for col in ("steps", "screen_after_11pm_min"):
        if col in df:
            df[f"{col}_7d"] = df[col].rolling(7, min_periods=3).mean()
    return df
