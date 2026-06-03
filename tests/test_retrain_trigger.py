import json
import os

import pytest

from src.services.retrain_trigger import check_drift, should_retrain
from src.services.data_loader import MODEL_FEATURES

_STATS_PATH = os.path.join(
    os.path.dirname(__file__), "..", "src", "model", "trained", "training_stats.json"
)

with open(_STATS_PATH) as f:
    _STATS = json.load(f)

_MEANS = {feat: _STATS[feat]["mean"] for feat in MODEL_FEATURES if feat in _STATS}


def _readings_at_mean(n=100, overrides=None):
    overrides = overrides or {}
    reading = {f: _MEANS.get(f, 5.0) for f in MODEL_FEATURES}
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
    # Use lag_1 — it has a non-zero training mean, so 20% above will trigger
    feat = "lag_1"
    mean = _MEANS.get(feat, 500.0)
    if mean == 0:
        pytest.skip("lag_1 training mean is 0 — cannot compute percentage deviation")
    high_val = mean * 1.20
    readings = _readings_at_mean(n=100, overrides={feat: high_val})
    result = check_drift(readings)
    assert result["drift_detected"] is True
    assert feat in result["drifted_features"]
    assert abs(result["deviations"][feat] - 20.0) < 0.01


def test_check_drift_feature_just_below_threshold_not_flagged():
    feat = "lag_1"
    mean = _MEANS.get(feat, 500.0)
    if mean == 0:
        pytest.skip("lag_1 training mean is 0")
    low_val = mean * 1.14
    readings = _readings_at_mean(n=100, overrides={feat: low_val})
    result = check_drift(readings)
    assert feat not in result["drifted_features"]


def test_check_drift_deviations_contains_all_model_features():
    readings = _readings_at_mean(n=100)
    result = check_drift(readings)
    for feat in MODEL_FEATURES:
        assert feat in result["deviations"], f"missing {feat} in deviations"


# --- should_retrain tests ---

def test_should_retrain_all_conditions_true_returns_true():
    assert should_retrain(True, 2000, 2200) is True


def test_should_retrain_drift_false_returns_false():
    assert should_retrain(False, 2000, 2200) is False


def test_should_retrain_clean_count_below_threshold_returns_false():
    assert should_retrain(True, 1999, 1999) is False


def test_should_retrain_anomaly_rate_too_high_returns_false():
    assert should_retrain(True, 2000, 3000) is False


def test_should_retrain_c1_c2_both_false_returns_false():
    assert should_retrain(False, 1999, 1999) is False


def test_should_retrain_c1_c3_both_false_returns_false():
    assert should_retrain(False, 2000, 3000) is False


def test_should_retrain_c2_c3_both_false_returns_false():
    assert should_retrain(True, 1000, 3000) is False


def test_should_retrain_all_conditions_false_returns_false():
    assert should_retrain(False, 1000, 3000) is False


# --- run_retraining tests ---

import pandas as pd
from unittest.mock import patch, MagicMock


def _make_train_df(n=500) -> pd.DataFrame:
    import numpy as np
    rng = np.random.default_rng(42)
    df = pd.DataFrame(rng.random((n, len(MODEL_FEATURES))), columns=MODEL_FEATURES)
    df["aggregate_wh"] = rng.uniform(100, 1000, n)
    return df


def test_run_retraining_returns_best_model_and_r2():
    from scripts.run_retraining import run_retraining
    with patch("scripts.run_retraining._load_base_data", return_value=_make_train_df()), \
         patch("scripts.run_retraining.fetch_clean_rows", return_value=[]), \
         patch("scripts.run_retraining.train_all_models") as mock_train:
        mock_train.return_value = (MagicMock(), 0.85)
        result = run_retraining()
    assert set(result.keys()) == {"best_model", "new_r2", "rows_used"}
    assert isinstance(result["new_r2"], float)
    assert -1.0 <= result["new_r2"] <= 1.0


def test_run_retraining_uses_only_model_features_as_X():
    from scripts.run_retraining import run_retraining
    captured = {}

    def capture_train(X_train, y_train, X_test, y_test):
        captured["columns"] = list(X_train.columns)
        return (MagicMock(), 0.80)

    with patch("scripts.run_retraining._load_base_data", return_value=_make_train_df()), \
         patch("scripts.run_retraining.fetch_clean_rows", return_value=[]), \
         patch("scripts.run_retraining.train_all_models", side_effect=capture_train):
        run_retraining()
    assert set(captured["columns"]) == set(MODEL_FEATURES)


def test_run_retraining_uses_time_ordered_split():
    from scripts.run_retraining import run_retraining
    captured = {}

    def capture_train(X_train, y_train, X_test, y_test):
        captured["n_train"] = len(X_train)
        captured["n_test"] = len(X_test)
        return (MagicMock(), 0.80)

    df = _make_train_df(n=500)
    with patch("scripts.run_retraining._load_base_data", return_value=df), \
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
        {"low_confidence": False, "input_features": {f: 5.0 for f in MODEL_FEATURES}, "aggregate_wh": 100.0},
        {"low_confidence": True,  "input_features": {f: 5.0 for f in MODEL_FEATURES}, "aggregate_wh": 500.0},
        {"low_confidence": False, "input_features": {f: 5.0 for f in MODEL_FEATURES}, "aggregate_wh": 90.0},
    ]
    with patch("scripts.run_retraining._load_base_data", return_value=_make_train_df(n=100)), \
         patch("scripts.run_retraining.fetch_clean_rows", return_value=supabase_rows), \
         patch("scripts.run_retraining.train_all_models", side_effect=capture_train):
        result = run_retraining()
    assert result["rows_used"] == 102


def test_run_retraining_uses_base_data_when_supabase_empty():
    from scripts.run_retraining import run_retraining
    with patch("scripts.run_retraining._load_base_data", return_value=_make_train_df(n=200)), \
         patch("scripts.run_retraining.fetch_clean_rows", return_value=[]), \
         patch("scripts.run_retraining.train_all_models") as mock_train:
        mock_train.return_value = (MagicMock(), 0.75)
        result = run_retraining()
    assert result["rows_used"] == 200
    assert result["new_r2"] == 0.75


# --- run_retraining_if_ready tests ---

import json as _json
from unittest.mock import patch, MagicMock, mock_open


_META_OLD = {"r2": 0.75}
_META_HIGHER = {"best_model": MagicMock(), "new_r2": 0.85, "rows_used": 2500}
_META_LOWER  = {"best_model": MagicMock(), "new_r2": 0.60, "rows_used": 2500}


def test_run_retraining_if_ready_skips_when_should_retrain_false():
    from src.services import retrain_trigger
    with patch.object(retrain_trigger, "should_retrain", return_value=False), \
         patch("scripts.run_retraining.run_retraining") as mock_run:
        retrain_trigger.run_retraining_if_ready(
            drift_detected=False, clean_row_count=100, total_row_count=110
        )
    mock_run.assert_not_called()


def test_run_retraining_if_ready_replaces_model_when_new_r2_higher():
    from src.services import retrain_trigger
    mock_supabase = MagicMock()
    with patch.object(retrain_trigger, "should_retrain", return_value=True), \
         patch.object(retrain_trigger, "_read_meta", return_value=_META_OLD), \
         patch("scripts.run_retraining.run_retraining", return_value=_META_HIGHER), \
         patch("joblib.dump") as mock_dump, \
         patch("src.services.retrain_trigger.supabase", mock_supabase):
        retrain_trigger.run_retraining_if_ready(
            drift_detected=True, clean_row_count=2000, total_row_count=2200
        )
    mock_dump.assert_called_once()
    insert_call = mock_supabase.table.return_value.insert.call_args[0][0]
    assert insert_call["model_replaced"] is True


def test_run_retraining_if_ready_keeps_model_when_new_r2_lower():
    from src.services import retrain_trigger
    mock_supabase = MagicMock()
    with patch.object(retrain_trigger, "should_retrain", return_value=True), \
         patch.object(retrain_trigger, "_read_meta", return_value=_META_OLD), \
         patch("scripts.run_retraining.run_retraining", return_value=_META_LOWER), \
         patch("joblib.dump") as mock_dump, \
         patch("src.services.retrain_trigger.supabase", mock_supabase):
        retrain_trigger.run_retraining_if_ready(
            drift_detected=True, clean_row_count=2000, total_row_count=2200
        )
    mock_dump.assert_not_called()
    insert_call = mock_supabase.table.return_value.insert.call_args[0][0]
    assert insert_call["model_replaced"] is False


def test_run_retraining_if_ready_resets_drift_flag_after_retrain():
    from src.services import retrain_trigger
    retrain_trigger._drift_first_detected = "2013-12-01T00:00:00"
    with patch.object(retrain_trigger, "should_retrain", return_value=True), \
         patch.object(retrain_trigger, "_read_meta", return_value=_META_OLD), \
         patch("scripts.run_retraining.run_retraining", return_value=_META_HIGHER), \
         patch("joblib.dump"), \
         patch("src.services.retrain_trigger.supabase", MagicMock()):
        retrain_trigger.run_retraining_if_ready(
            drift_detected=True, clean_row_count=2000, total_row_count=2200
        )
    assert retrain_trigger._drift_first_detected is None


def test_run_retraining_if_ready_inserts_retrain_log_row():
    from src.services import retrain_trigger
    mock_supabase = MagicMock()
    with patch.object(retrain_trigger, "should_retrain", return_value=True), \
         patch.object(retrain_trigger, "_read_meta", return_value=_META_OLD), \
         patch("scripts.run_retraining.run_retraining", return_value=_META_HIGHER), \
         patch("joblib.dump"), \
         patch("src.services.retrain_trigger.supabase", mock_supabase):
        retrain_trigger.run_retraining_if_ready(
            drift_detected=True, clean_row_count=2000, total_row_count=2200
        )
    inserted = mock_supabase.table.return_value.insert.call_args[0][0]
    assert {"model_replaced", "old_model_r2", "new_model_r2", "rows_used"}.issubset(
        inserted.keys()
    )
    mock_supabase.table.return_value.insert.return_value.execute.assert_called_once()


def test_run_retraining_if_ready_calls_correct_table():
    from src.services import retrain_trigger
    mock_supabase = MagicMock()
    with patch.object(retrain_trigger, "should_retrain", return_value=True), \
         patch.object(retrain_trigger, "_read_meta", return_value=_META_OLD), \
         patch("scripts.run_retraining.run_retraining", return_value=_META_HIGHER), \
         patch("joblib.dump"), \
         patch("src.services.retrain_trigger.supabase", mock_supabase):
        retrain_trigger.run_retraining_if_ready(
            drift_detected=True, clean_row_count=2000, total_row_count=2200
        )
    mock_supabase.table.assert_called_with("retrain_log")


def test_scheduler_calls_run_retraining_if_ready_after_drift_check():
    import src.services.scheduler as sched
    from tests.test_scheduler import _make_test_row
    sched._clean_reading_count = 99
    mock_clean_rows = [{feat: 5.0 for feat in MODEL_FEATURES} for _ in range(100)]
    drift_result = {"drift_detected": True, "drifted_features": ["lag_1"], "deviations": {"lag_1": 20.0}}

    with patch("src.services.scheduler._get_next_test_row", return_value=_make_test_row()), \
         patch("src.services.scheduler._get_scaler", return_value=None), \
         patch("src.services.scheduler.predict_full", return_value=150.0), \
         patch("src.services.scheduler.wh_to_cost", return_value=(0.15, 0.05)), \
         patch("src.services.scheduler.insert_prediction"), \
         patch("src.services.scheduler.monitor_reading", return_value={"low_confidence": False}), \
         patch("src.services.scheduler.get_last_n_clean_readings", return_value=mock_clean_rows), \
         patch("src.services.scheduler.check_drift", return_value=drift_result), \
         patch("src.services.scheduler.store_drift_event"), \
         patch("src.services.scheduler.fetch_row_counts", return_value=(2100, 2300)), \
         patch("src.services.scheduler.run_retraining_if_ready") as mock_retrain:
        from src.services.scheduler import submit_smart_home_reading
        submit_smart_home_reading()
    mock_retrain.assert_called_once()


# --- retrain status endpoint tests ---

from fastapi.testclient import TestClient


_RETRAIN_LOG_ROW = {
    "timestamp": "2013-12-16T10:00:00+00:00",
    "old_model_r2": 0.75,
    "new_model_r2": 0.85,
    "model_replaced": True,
    "rows_used": 2500,
}

_RETRAIN_LOG_ROW_NOT_REPLACED = {**_RETRAIN_LOG_ROW, "model_replaced": False}


def _client():
    from src.api.main import app
    return TestClient(app)


def test_retrain_status_returns_200_with_correct_shape():
    mock_db = MagicMock()
    mock_db.table.return_value.select.return_value.order.return_value \
        .limit.return_value.execute.return_value.data = [_RETRAIN_LOG_ROW]
    with patch("src.api.routes.supabase", mock_db):
        response = _client().get("/api/v1/monitor/retrain")
    assert response.status_code == 200
    body = response.json()
    assert {"timestamp", "old_model_r2", "new_model_r2", "model_replaced", "rows_used"} \
        .issubset(body.keys())


def test_retrain_status_model_replaced_true_reflected_in_response():
    mock_db = MagicMock()
    mock_db.table.return_value.select.return_value.order.return_value \
        .limit.return_value.execute.return_value.data = [_RETRAIN_LOG_ROW]
    with patch("src.api.routes.supabase", mock_db):
        response = _client().get("/api/v1/monitor/retrain")
    assert response.json()["model_replaced"] is True


def test_retrain_status_model_replaced_false_reflected_in_response():
    mock_db = MagicMock()
    mock_db.table.return_value.select.return_value.order.return_value \
        .limit.return_value.execute.return_value.data = [_RETRAIN_LOG_ROW_NOT_REPLACED]
    with patch("src.api.routes.supabase", mock_db):
        response = _client().get("/api/v1/monitor/retrain")
    assert response.json()["model_replaced"] is False


def test_retrain_status_returns_404_when_no_rows():
    mock_db = MagicMock()
    mock_db.table.return_value.select.return_value.order.return_value \
        .limit.return_value.execute.return_value.data = []
    with patch("src.api.routes.supabase", mock_db):
        response = _client().get("/api/v1/monitor/retrain")
    assert response.status_code == 404


def test_retrain_status_returns_500_on_supabase_error():
    mock_db = MagicMock()
    mock_db.table.return_value.select.return_value.order.return_value \
        .limit.return_value.execute.side_effect = Exception("supabase unreachable")
    with patch("src.api.routes.supabase", mock_db):
        response = _client().get("/api/v1/monitor/retrain")
    assert response.status_code == 500
