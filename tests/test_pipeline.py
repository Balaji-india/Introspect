import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from introspect import baseline, consent, config, features, forecast, ingest, narrate, pipeline, privacy, why  # noqa: E402
from introspect.synthetic import generate  # noqa: E402


@pytest.fixture(scope="module")
def data_dir(tmp_path_factory):
    return generate(tmp_path_factory.mktemp("data"), days=60, seed=7)


@pytest.fixture(scope="module")
def frame(data_dir):
    return baseline.compute_baseline(features.add_features(ingest.build_timeline(data_dir)))


@pytest.fixture(autouse=True)
def isolated_state(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "STATE_DIR", tmp_path / "state")


def test_ingest_builds_one_row_per_day(data_dir):
    df = ingest.build_timeline(data_dir)
    assert len(df) == 60
    assert df["date"].is_unique
    for col in ("steps", "sleep_min", "resting_hr", "hrv", "screen_after_11pm_min", "is_exam_day"):
        assert col in df


def test_no_personal_alerts_before_cold_start(frame):
    assert frame["sleep_min_z"].iloc[: config.MIN_BASELINE_DAYS].isna().all()


def test_planted_bad_night_is_flagged(frame):
    bad = frame.iloc[-4]                       # synthetic.generate plants it at n-4
    assert bad["is_anomaly"]
    assert {"sleep_min", "resting_hr", "hrv"} <= set(bad["drift_metrics"])


def test_why_engine_finds_screen_time_to_sleep(frame):
    ins = why.find_insights(frame)
    top = ins[0]
    assert top.driver == "screen_after_11pm_min" and top.outcome == "sleep"
    assert top.rho < -0.3 and top.p_value < 0.05 and top.effect < 0


def test_forecast_is_monotonic_in_screen_time(frame):
    f = forecast.train_and_forecast(frame)
    assert f["status"] == "ok"
    w = f["what_if"]
    assert w["screens_off_by_11pm"] >= w["usual_night"] >= w["late_night_2h"]
    assert f["eval"]["test_mae"] < f["eval"]["personal_mean_mae"]


def test_privacy_gateway_blocks_raw_data_and_needs_consent(data_dir):
    res = pipeline.run(data_dir)
    facts = res["facts"]
    assert "timeline" not in facts and "date" not in facts and "Id" not in str(facts)
    with pytest.raises(ValueError):
        privacy.check({**facts, "raw_heart_rate": [60, 61]})
    with pytest.raises(privacy.ConsentError):
        privacy.release(facts, "cloud_narration")          # off by default
    consent.update("purposes", "cloud_narration", True)
    assert privacy.release(facts, "cloud_narration") == facts


def test_llm_output_must_be_grounded(data_dir):
    facts = pipeline.run(data_dir)["facts"]
    ok = f"Your readiness today is {round(facts['readiness_today'])}."
    assert narrate.grounded(ok, facts)
    assert not narrate.grounded("You slept 9999 minutes and burned 12345 calories.", facts)


def test_template_brief_mentions_action(data_dir):
    res = pipeline.run(data_dir)
    assert res["brief"]["source"] == "template"
    assert res["facts"]["suggested_action"] in res["brief"]["text"]


def test_bedrock_path_uses_guardrail_and_falls_back(data_dir, monkeypatch):
    """Bedrock call shape (Converse API + Guardrails) without real AWS credentials."""
    import boto3

    calls = {}

    class FakeClient:
        def __init__(self, text):
            self.text = text

        def converse(self, **kw):
            calls.update(kw)
            return {"output": {"message": {"content": [{"text": self.text}]}}}

    facts = pipeline.run(data_dir)["facts"]
    consent.update("purposes", "cloud_narration", True)
    monkeypatch.setattr(config, "USE_BEDROCK", True)
    monkeypatch.setattr(config, "BEDROCK_GUARDRAIL_ID", "gr-123")

    good = f"Readiness is {round(facts['readiness_today'])} today. " + facts["suggested_action"]
    monkeypatch.setattr(boto3, "client", lambda *a, **k: FakeClient(good))
    out = narrate.daily_brief(facts)
    assert out["source"] == "bedrock"
    assert calls["guardrailConfig"]["guardrailIdentifier"] == "gr-123"
    assert "Facts:" in calls["messages"][0]["content"][0]["text"]

    monkeypatch.setattr(boto3, "client", lambda *a, **k: FakeClient("You burned 98765 calories!"))
    assert narrate.daily_brief(facts)["source"] == "template"     # ungrounded number -> rejected


def test_loader_reads_raw_kaggle_fitbit_format(tmp_path):
    """Public Kaggle export: many users, per-second heart rate, no HRV."""
    import pandas as pd

    rows, sleep, hr = [], [], []
    for uid in (111, 222):
        for d in range(1, 11):
            date = f"4/{d}/2016"
            rows.append({"Id": uid, "ActivityDate": date, "TotalSteps": 5000 + d, "VeryActiveMinutes": 10,
                         "SedentaryMinutes": 700, "Calories": 2000})
            sleep.append({"Id": uid, "SleepDay": f"{date} 12:00:00 AM", "TotalSleepRecords": 1,
                          "TotalMinutesAsleep": 400, "TotalTimeInBed": 430})
            for s, v in ((0, 58), (1, 60), (2, 95)):
                hr.append({"Id": uid, "Time": f"{date} 7:00:0{s} AM", "Value": v})
    rows.append({"Id": 111, "ActivityDate": "4/11/2016", "TotalSteps": 1, "VeryActiveMinutes": 0,
                 "SedentaryMinutes": 1, "Calories": 1})
    pd.DataFrame(rows).to_csv(tmp_path / "dailyActivity_merged.csv", index=False)
    pd.DataFrame(sleep).to_csv(tmp_path / "sleepDay_merged.csv", index=False)
    pd.DataFrame(hr).to_csv(tmp_path / "heartrate_seconds_merged.csv", index=False)

    df = ingest.build_timeline(tmp_path)          # picks the user with most days (111)
    assert len(df) == 11 and df["sleep_min"].iloc[0] == 400
    assert 58 <= df["resting_hr"].iloc[0] < 60   # 5th percentile of the day's HR
    df2 = ingest.build_timeline(tmp_path, user_id=222)
    assert len(df2) == 10


def test_cached_fit_predicts_same_as_retraining(frame):
    fitted = forecast.fit(frame)
    for screen in (0, 60, 150):
        assert forecast.predict(fitted, planned_screen_min=screen) == \
            forecast.train_and_forecast(frame, planned_screen_min=screen)
