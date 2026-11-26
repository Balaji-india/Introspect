"""Synthetic wearable + phone data in the public Fitbit export schema.

Used for demos and tests so nobody's real health data is needed. The generator plants
known relationships (late screen time -> less sleep -> higher resting HR, exam week
stress) so we can check that the baseline and why-engine recover them.

Output files (same column names as the public "Fitbit Fitness Tracker Data" export):
  dailyActivity_merged.csv, sleepDay_merged.csv, heartrateDaily.csv
plus Introspect-specific phone/calendar sources:
  screen_time.csv, calendar.csv, checkins.csv
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

USER_ID = 1503960366  # matches the style of Fitbit export ids

# Demo scenarios ("watch it detect live"). "default" reproduces data/sample exactly.
#   normal:    no exam week, no planted bad night
#   exam_week: a 7-day exam week that ends yesterday, with more late-night screen time
#   bad_night: the planted bad night is last night (the latest day), so today's brief changes
SCENARIOS = ("default", "normal", "exam_week", "bad_night")


def generate(out_dir: str | Path, days: int = 60, seed: int = 7, end: str = "2026-11-23",
             scenario: str = "default") -> Path:
    if scenario not in SCENARIOS:
        raise ValueError(f"unknown scenario {scenario!r}; choose from {SCENARIOS}")
    rng = np.random.default_rng(seed)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    dates = pd.date_range(end=end, periods=days, freq="D")
    n = len(dates)

    weekend = dates.day_of_week >= 5
    exam = np.zeros(n, dtype=bool)
    if scenario in ("default", "bad_night"):
        exam[n - 16 : n - 9] = True      # one exam week, two weeks ago
    elif scenario == "exam_week":
        exam[n - 8 : n - 1] = True       # exam week ending yesterday (today is n-1)

    # Phone: minutes of screen time after 11 pm (bursty, worse in exam week)
    screen_late = rng.gamma(2.0, 22.0, n) + np.where(weekend, 25, 0) + np.where(exam, 45, 0)
    if scenario == "exam_week":
        screen_late = screen_late + np.where(exam, 30, 0)   # cramming: even more late-night phone time
    screen_late = np.clip(screen_late, 0, 240)

    # Sleep responds to late screen time and exams
    sleep = 445 - 0.42 * screen_late - np.where(exam, 25, 0) + rng.normal(0, 18, n)
    sleep = np.clip(sleep, 240, 560)
    time_in_bed = sleep + rng.normal(28, 8, n).clip(5, None)

    # Activity
    steps = rng.normal(7800, 1800, n) - np.where(exam, 2600, 0) + np.where(weekend, 900, 0)
    steps = np.clip(steps, 900, 18000).round()
    very_active = np.clip(steps / 400 + rng.normal(0, 4, n), 0, None).round()
    sedentary = np.clip(1440 - sleep - steps / 90 + rng.normal(0, 30, n), 300, 1200).round()
    calories = (1650 + steps * 0.045 + rng.normal(0, 90, n)).round()

    # Resting HR rises after short sleep and during exams; HRV falls
    sleep_debt = np.r_[0, (445 - sleep)[:-1]]          # previous night
    resting_hr = 63 + 0.035 * sleep_debt + np.where(exam, 3.5, 0) + rng.normal(0, 1.4, n)
    hrv = 58 - 0.06 * sleep_debt - np.where(exam, 7, 0) + rng.normal(0, 3.5, n)

    # One clear anomaly: a short night out with elevated resting HR and low HRV (for the demo)
    k = {"default": n - 4, "bad_night": n - 1}.get(scenario)
    if k is not None:
        sleep[k] = 262
        resting_hr[k] = 76
        hrv[k] = 31

    # Calendar & check-ins
    events = (rng.poisson(2.2, n) + np.where(exam, 3, 0)).astype(int)
    mood = np.clip(np.round(3.6 + (sleep - 420) / 90 - np.where(exam, 0.8, 0) + rng.normal(0, 0.5, n)), 1, 5)

    d = dates.strftime("%m/%d/%Y")
    pd.DataFrame({
        "Id": USER_ID, "ActivityDate": d, "TotalSteps": steps.astype(int),
        "TotalDistance": (steps * 0.00076).round(2), "VeryActiveMinutes": very_active.astype(int),
        "FairlyActiveMinutes": (very_active * 0.6).round().astype(int),
        "LightlyActiveMinutes": (steps / 45).round().astype(int),
        "SedentaryMinutes": sedentary.astype(int), "Calories": calories.astype(int),
    }).to_csv(out / "dailyActivity_merged.csv", index=False)

    pd.DataFrame({
        "Id": USER_ID, "SleepDay": dates.strftime("%m/%d/%Y 12:00:00 AM"), "TotalSleepRecords": 1,
        "TotalMinutesAsleep": sleep.round().astype(int), "TotalTimeInBed": time_in_bed.round().astype(int),
    }).to_csv(out / "sleepDay_merged.csv", index=False)

    pd.DataFrame({
        "Id": USER_ID, "Date": d, "RestingHeartRate": resting_hr.round(1), "HRV_RMSSD": hrv.round(1),
    }).to_csv(out / "heartrateDaily.csv", index=False)

    pd.DataFrame({"date": dates.strftime("%Y-%m-%d"), "screen_after_11pm_min": screen_late.round().astype(int),
                  "total_screen_min": (screen_late + rng.normal(260, 50, n)).round().astype(int)}
                 ).to_csv(out / "screen_time.csv", index=False)
    pd.DataFrame({"date": dates.strftime("%Y-%m-%d"), "events": events, "is_exam_day": exam.astype(int)}
                 ).to_csv(out / "calendar.csv", index=False)
    pd.DataFrame({"date": dates.strftime("%Y-%m-%d"), "mood_1to5": mood.astype(int)}
                 ).to_csv(out / "checkins.csv", index=False)
    return out


if __name__ == "__main__":
    import sys
    print("wrote", generate(sys.argv[1] if len(sys.argv) > 1 else "data/sample"))
