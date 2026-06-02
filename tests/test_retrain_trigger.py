import json
import os

import pytest

from src.services.retrain_trigger import check_drift, should_retrain

_STATS_PATH = os.path.join(
    os.path.dirname(__file__), "..", "src", "model", "trained", "training_stats.json"
)

with open(_STATS_PATH) as f:
    _STATS = json.load(f)

FULL_FEATURES = [
    "lights", "T1", "RH_1", "T2", "RH_2", "T3", "RH_3",
    "T4", "RH_4", "T5", "RH_5", "T6", "RH_6", "T7", "RH_7",
    "T8", "RH_8", "T9", "RH_9", "T_out", "Press_mm_hg",
    "RH_out", "Windspeed", "Visibility", "Tdewpoint",
]

_MEANS = {feat: _STATS[feat]["mean"] for feat in FULL_FEATURES}


def _readings_at_mean(n=100, overrides=None):
    overrides = overrides or {}
    reading = {f: _MEANS[f] for f in FULL_FEATURES}
    reading.update(overrides)
    return [dict(reading) for _ in range(n)]


# --- check_drift tests ---

def test_check_drift_raises_on_too_few_readings():
    readings = _readings_at_mean(n=99)
    with pytest.raises(ValueError):
        check_drift(readings)


def test_check_drift_no_drift_at_training_mean():
    readings = _readings_at_mean(n=100)
    result = check_drift(readings)
    assert result["drift_detected"] is False
    assert result["drifted_features"] == []


def test_check_drift_detects_feature_above_threshold():
    t1_high = _MEANS["T1"] * 1.20
    readings = _readings_at_mean(n=100, overrides={"T1": t1_high})
    result = check_drift(readings)
    assert result["drift_detected"] is True
    assert "T1" in result["drifted_features"]
    assert abs(result["deviations"]["T1"] - 20.0) < 0.01


def test_check_drift_feature_just_below_threshold_not_flagged():
    rh1_low = _MEANS["RH_1"] * 1.14
    readings = _readings_at_mean(n=100, overrides={"RH_1": rh1_low})
    result = check_drift(readings)
    assert result["drift_detected"] is False
    assert "RH_1" not in result["drifted_features"]


def test_check_drift_deviations_contains_all_25_features():
    readings = _readings_at_mean(n=100)
    result = check_drift(readings)
    assert len(result["deviations"]) == 25
    assert "lights" in result["deviations"]
    assert "Tdewpoint" in result["deviations"]


# --- should_retrain tests ---

def test_should_retrain_all_conditions_true_returns_true():
    # 2000 / 2200 = 0.909 — passes 90% threshold
    assert should_retrain(True, 2000, 2200) is True


def test_should_retrain_drift_false_returns_false():
    assert should_retrain(False, 2000, 2200) is False


def test_should_retrain_clean_count_below_threshold_returns_false():
    # 1999 < 2000 — fails C2
    assert should_retrain(True, 1999, 1999) is False


def test_should_retrain_anomaly_rate_too_high_returns_false():
    # 2000 / 3000 = 0.667 — fails C3
    assert should_retrain(True, 2000, 3000) is False


def test_should_retrain_c1_c2_both_false_returns_false():
    assert should_retrain(False, 1999, 1999) is False


def test_should_retrain_c1_c3_both_false_returns_false():
    assert should_retrain(False, 2000, 3000) is False


def test_should_retrain_c2_c3_both_false_returns_false():
    # 1000 / 3000 = 0.333 — fails C2 and C3
    assert should_retrain(True, 1000, 3000) is False


def test_should_retrain_all_conditions_false_returns_false():
    assert should_retrain(False, 1000, 3000) is False
