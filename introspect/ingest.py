"""Ingest + normalise sources into one daily timeline (one row per day).

Supported today:
  * Fitbit / Google export CSVs (public Kaggle "Fitbit Fitness Tracker Data" schema)
  * Screen-time CSV (Android UsageStats export), calendar CSV, 1-tap check-ins
Planned: Android Health Connect + Apple HealthKit XML importers (see README roadmap).
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd


def _read(path: Path) -> pd.DataFrame | None:
    return pd.read_csv(path) if path.exists() else None


def load_fitbit_export(folder: str | Path, user_id: int | None = None) -> pd.DataFrame:
    folder = Path(folder)
    act = _read(folder / "dailyActivity_merged.csv")
    if act is None:
        raise FileNotFoundError(f"dailyActivity_merged.csv not found in {folder}")
    if user_id is None:
        user_id = int(act["Id"].mode().iloc[0])      # Kaggle export has many users; pick one
    act = act[act["Id"] == user_id].copy()
    act["date"] = pd.to_datetime(act["ActivityDate"], format="%m/%d/%Y")
    df = act.rename(columns={"TotalSteps": "steps", "VeryActiveMinutes": "very_active_min",
                             "SedentaryMinutes": "sedentary_min", "Calories": "calories"})[
        ["date", "steps", "very_active_min", "sedentary_min", "calories"]]

    sleep = _read(folder / "sleepDay_merged.csv")
    if sleep is not None:
        sleep = sleep[sleep["Id"] == user_id].copy()
        sleep["date"] = pd.to_datetime(sleep["SleepDay"], format="%m/%d/%Y %I:%M:%S %p").dt.normalize()
        sleep = sleep.groupby("date", as_index=False).agg(sleep_min=("TotalMinutesAsleep", "sum"),
                                                           in_bed_min=("TotalTimeInBed", "sum"))
        df = df.merge(sleep, on="date", how="left")

    hr = _read(folder / "heartrateDaily.csv")
    if hr is not None:
        hr = hr[hr["Id"] == user_id].copy()
        hr["date"] = pd.to_datetime(hr["Date"], format="%m/%d/%Y")
        df = df.merge(hr.rename(columns={"RestingHeartRate": "resting_hr", "HRV_RMSSD": "hrv"})[
            ["date", "resting_hr", "hrv"]], on="date", how="left")
    else:
        # Raw Kaggle export only has per-second HR: estimate resting HR as the daily 5th percentile
        raw = _read(folder / "heartrate_seconds_merged.csv")
        if raw is not None:
            raw = raw[raw["Id"] == user_id].copy()
            raw["date"] = pd.to_datetime(raw["Time"], format="%m/%d/%Y %I:%M:%S %p").dt.normalize()
            rhr = raw.groupby("date")["Value"].quantile(0.05).rename("resting_hr").reset_index()
            df = df.merge(rhr, on="date", how="left")
    return df


def load_phone_and_calendar(folder: str | Path) -> pd.DataFrame | None:
    folder = Path(folder)
    parts = []
    for name in ("screen_time.csv", "calendar.csv", "checkins.csv"):
        d = _read(folder / name)
        if d is not None:
            d["date"] = pd.to_datetime(d["date"])
            parts.append(d)
    if not parts:
        return None
    out = parts[0]
    for p in parts[1:]:
        out = out.merge(p, on="date", how="outer")
    return out


def build_timeline(folder: str | Path, user_id: int | None = None) -> pd.DataFrame:
    """Merge every available source into one tidy daily timeline."""
    df = load_fitbit_export(folder, user_id)
    phone = load_phone_and_calendar(folder)
    if phone is not None:
        df = df.merge(phone, on="date", how="left")
    df = df.sort_values("date").drop_duplicates("date").reset_index(drop=True)
    # Wearables drop days (watch not worn). Mark them instead of inventing values.
    df["has_sleep"] = df.get("sleep_min", pd.Series(index=df.index, dtype=float)).notna()
    return df
