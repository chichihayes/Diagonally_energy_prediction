import pytest
import pandas as pd
from unittest.mock import patch, MagicMock

from src.services.data_loader import MODEL_FEATURES, APPLIANCE_COLS
from src.services.scheduler import submit_smart_home_reading


def _make_test_row() -> pd.Series:
    """A minimal test-split row with all expected columns."""
    data = {feat: 5.0 for feat in MODEL_FEATURES}
    for col in APPLIANCE_COLS:
        data[col] = 10.0
    data["aggregate_wh"] = sum(data[col] for col in APPLIANCE_COLS)
    return pd.Series(data)


@pytest.fixture(autouse=True)
def patch_test_row(monkeypatch):
    monkeypatch.setattr("src.services.scheduler._get_next_test_row", _make_test_row)


def test_submit_smart_home_reading_calls_insert_on_success():
    mock_insert = MagicMock()
    with patch("src.services.scheduler.wh_to_cost", return_value=(0.09, 0.03)), \
         patch("src.services.scheduler.insert_prediction", mock_insert):
        submit_smart_home_reading()
    mock_insert.assert_called_once()
    call_row = mock_insert.call_args[0][0]
    assert call_row["tier"] == "full"
    assert call_row["predicted_wh"] == 90.0


def test_submit_smart_home_reading_returns_on_db_exception():
    with patch("src.services.scheduler.wh_to_cost", return_value=(0.09, 0.03)), \
         patch("src.services.scheduler.insert_prediction",
               side_effect=RuntimeError("supabase write failed")):
        result = submit_smart_home_reading()
    assert result is None


def test_scheduler_is_running_after_app_startup():
    from fastapi.testclient import TestClient
    from src.api.main import app, scheduler
    with TestClient(app):
        assert scheduler.running is True


import src.services.scheduler as scheduler_module


def test_scheduler_increments_clean_reading_count_on_non_anomalous_tick():
    scheduler_module._clean_reading_count = 0
    with patch("src.services.scheduler.wh_to_cost", return_value=(0.09, 0.03)), \
         patch("src.services.scheduler.insert_prediction"), \
         patch("src.services.scheduler.check_anomaly", return_value={"is_anomaly": False, "z_scores": {}, "flagged_features": []}):
        submit_smart_home_reading()
    assert scheduler_module._clean_reading_count == 1


def test_scheduler_does_not_increment_count_on_anomalous_tick():
    scheduler_module._clean_reading_count = 0
    with patch("src.services.scheduler.wh_to_cost", return_value=(0.09, 0.03)), \
         patch("src.services.scheduler.insert_prediction"), \
         patch("src.services.scheduler.store_anomaly"), \
         patch("src.services.scheduler.check_anomaly", return_value={"is_anomaly": True, "z_scores": {}, "flagged_features": []}):
        submit_smart_home_reading()
    assert scheduler_module._clean_reading_count == 0


def test_scheduler_triggers_drift_check_at_100_and_resets_counter():
    scheduler_module._clean_reading_count = 99
    mock_clean_rows = [{feat: 5.0 for feat in MODEL_FEATURES} for _ in range(100)]
    drift_result = {"drift_detected": False, "drifted_features": [], "deviations": {}}
    with patch("src.services.scheduler.wh_to_cost", return_value=(0.09, 0.03)), \
         patch("src.services.scheduler.insert_prediction"), \
         patch("src.services.scheduler.check_anomaly", return_value={"is_anomaly": False, "z_scores": {}, "flagged_features": []}), \
         patch("src.services.scheduler.get_last_n_clean_readings", return_value=mock_clean_rows) as mock_fetch, \
         patch("src.services.scheduler.check_drift", return_value=drift_result) as mock_drift, \
         patch("src.services.scheduler.store_drift_event") as mock_store:
        submit_smart_home_reading()
    mock_drift.assert_called_once_with(mock_clean_rows)
    mock_store.assert_called_once()
    assert scheduler_module._clean_reading_count == 0


def test_scheduler_does_not_trigger_drift_check_below_100():
    scheduler_module._clean_reading_count = 50
    with patch("src.services.scheduler.wh_to_cost", return_value=(0.09, 0.03)), \
         patch("src.services.scheduler.insert_prediction"), \
         patch("src.services.scheduler.check_anomaly", return_value={"is_anomaly": False, "z_scores": {}, "flagged_features": []}), \
         patch("src.services.scheduler.check_drift") as mock_drift, \
         patch("src.services.scheduler.store_drift_event") as mock_store:
        submit_smart_home_reading()
    mock_drift.assert_not_called()
    mock_store.assert_not_called()
    assert scheduler_module._clean_reading_count == 51


def test_scheduler_resets_counter_and_skips_drift_check_on_fetch_failure():
    scheduler_module._clean_reading_count = 99
    with patch("src.services.scheduler.wh_to_cost", return_value=(0.09, 0.03)), \
         patch("src.services.scheduler.insert_prediction"), \
         patch("src.services.scheduler.check_anomaly", return_value={"is_anomaly": False, "z_scores": {}, "flagged_features": []}), \
         patch("src.services.scheduler.get_last_n_clean_readings", side_effect=Exception("connection timeout")), \
         patch("src.services.scheduler.check_drift") as mock_drift, \
         patch("src.services.scheduler.store_drift_event") as mock_store:
        submit_smart_home_reading()
    mock_drift.assert_not_called()
    mock_store.assert_not_called()
    assert scheduler_module._clean_reading_count == 0


def test_scheduler_stores_per_appliance_values():
    mock_insert = MagicMock()
    with patch("src.services.scheduler.wh_to_cost", return_value=(0.09, 0.03)), \
         patch("src.services.scheduler.insert_prediction", mock_insert), \
         patch("src.services.scheduler.check_anomaly", return_value={"is_anomaly": False, "z_scores": {}, "flagged_features": []}):
        submit_smart_home_reading()
    call_row = mock_insert.call_args[0][0]
    assert "fridge_wh" in call_row
    assert "electric_heater_wh" in call_row
    assert "estimated_cost_gbp" in call_row
