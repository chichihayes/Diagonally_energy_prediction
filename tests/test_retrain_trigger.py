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


# --- run_retraining tests ---

import pandas as pd
from unittest.mock import patch, MagicMock

_UCI_COLUMNS = [
    "date", "Appliances", "lights",
    "T1", "RH_1", "T2", "RH_2", "T3", "RH_3", "T4", "RH_4",
    "T5", "RH_5", "T6", "RH_6", "T7", "RH_7", "T8", "RH_8",
    "T9", "RH_9", "T_out", "Press_mm_hg", "RH_out",
    "Windspeed", "Visibility", "Tdewpoint", "rv1", "rv2",
]


def _make_uci_df(n=500):
    import numpy as np
    rng = np.random.default_rng(42)
    df = pd.DataFrame(rng.random((n, len(_UCI_COLUMNS))), columns=_UCI_COLUMNS)
    df["date"] = pd.date_range("2016-01-01", periods=n, freq="10min")
    return df


def test_run_retraining_returns_best_model_and_r2():
    from scripts.run_retraining import run_retraining
    with patch("scripts.run_retraining.load_uci_csv", return_value=_make_uci_df()), \
         patch("scripts.run_retraining.fetch_clean_rows", return_value=[]), \
         patch("scripts.run_retraining.train_all_models") as mock_train:
        mock_train.return_value = (MagicMock(), 0.85)
        result = run_retraining()
    assert set(result.keys()) == {"best_model", "new_r2", "rows_used"}
    assert isinstance(result["new_r2"], float)
    assert -1.0 <= result["new_r2"] <= 1.0


def test_run_retraining_drops_rv1_rv2():
    from scripts.run_retraining import run_retraining
    captured = {}

    def capture_train(X_train, y_train, X_test, y_test):
        captured["columns"] = list(X_train.columns)
        return (MagicMock(), 0.80)

    with patch("scripts.run_retraining.load_uci_csv", return_value=_make_uci_df()), \
         patch("scripts.run_retraining.fetch_clean_rows", return_value=[]), \
         patch("scripts.run_retraining.train_all_models", side_effect=capture_train):
        run_retraining()
    assert "rv1" not in captured["columns"]
    assert "rv2" not in captured["columns"]


def test_run_retraining_uses_time_ordered_split():
    from scripts.run_retraining import run_retraining
    captured = {}

    def capture_train(X_train, y_train, X_test, y_test):
        captured["n_train"] = len(X_train)
        captured["n_test"] = len(X_test)
        return (MagicMock(), 0.80)

    df = _make_uci_df(n=500)
    with patch("scripts.run_retraining.load_uci_csv", return_value=df), \
         patch("scripts.run_retraining.fetch_clean_rows", return_value=[]), \
         patch("scripts.run_retraining.train_all_models", side_effect=capture_train):
        run_retraining()
    assert captured["n_train"] == 400
    assert captured["n_test"] == 100


def test_run_retraining_excludes_low_confidence_rows():
    from scripts.run_retraining import run_retraining
    captured = {}

    def capture_train(X_train, y_train, X_test, y_test):
        captured["total_rows"] = len(X_train) + len(X_test)
        return (MagicMock(), 0.80)

    supabase_rows = [
        {"low_confidence": False, "input_features": {"lights": 10, "T1": 19.0}},
        {"low_confidence": True,  "input_features": {"lights": 50, "T1": 30.0}},
        {"low_confidence": False, "input_features": {"lights": 5,  "T1": 18.0}},
    ]
    with patch("scripts.run_retraining.load_uci_csv", return_value=_make_uci_df(n=100)), \
         patch("scripts.run_retraining.fetch_clean_rows", return_value=supabase_rows), \
         patch("scripts.run_retraining.train_all_models", side_effect=capture_train):
        result = run_retraining()
    assert result["rows_used"] == 102


def test_run_retraining_uses_uci_csv_when_supabase_empty():
    from scripts.run_retraining import run_retraining
    with patch("scripts.run_retraining.load_uci_csv", return_value=_make_uci_df(n=200)), \
         patch("scripts.run_retraining.fetch_clean_rows", return_value=[]), \
         patch("scripts.run_retraining.train_all_models") as mock_train:
        mock_train.return_value = (MagicMock(), 0.75)
        result = run_retraining()
    assert result["rows_used"] == 200
    assert result["new_r2"] == 0.75
