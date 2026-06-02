import pytest
from unittest.mock import patch, MagicMock

from src.services.scheduler import submit_smart_home_reading

MOCK_WEATHER = {
    "T_out": 28.4, "Press_mm_hg": 1012.0,
    "RH_out": 82.0, "Windspeed": 3.1,
    "Visibility": 10.0, "Tdewpoint": 25.1,
}


@pytest.fixture(autouse=True)
def sensor_env(monkeypatch):
    monkeypatch.setenv("SENSOR_LOCATION", "Lagos")
    monkeypatch.setenv("SENSOR_LIGHTS", "0")
    for i in range(1, 10):
        monkeypatch.setenv(f"SENSOR_T{i}", "20.0")
        monkeypatch.setenv(f"SENSOR_RH_{i}", "50.0")


def test_submit_smart_home_reading_calls_insert_on_success():
    mock_insert = MagicMock()
    with patch("src.services.scheduler.get_weather", return_value=MOCK_WEATHER), \
         patch("src.services.scheduler.predict_full", return_value=150.0), \
         patch("src.services.scheduler.wh_to_cost", return_value=(0.15, 10.2)), \
         patch("src.services.scheduler.insert_prediction", mock_insert):
        submit_smart_home_reading()
    mock_insert.assert_called_once()
    call_row = mock_insert.call_args[0][0]
    assert call_row["tier"] == "full"
    assert call_row["predicted_wh"] == 150.0
    assert call_row["location"] == "Lagos"


def test_submit_smart_home_reading_returns_on_weather_exception():
    mock_insert = MagicMock()
    with patch("src.services.scheduler.get_weather",
               side_effect=RuntimeError("connection timeout")), \
         patch("src.services.scheduler.insert_prediction", mock_insert):
        result = submit_smart_home_reading()
    assert result is None
    mock_insert.assert_not_called()


def test_submit_smart_home_reading_returns_on_predict_exception():
    mock_insert = MagicMock()
    with patch("src.services.scheduler.get_weather", return_value=MOCK_WEATHER), \
         patch("src.services.scheduler.predict_full",
               side_effect=RuntimeError("model not loaded")), \
         patch("src.services.scheduler.insert_prediction", mock_insert):
        result = submit_smart_home_reading()
    assert result is None
    mock_insert.assert_not_called()


def test_submit_smart_home_reading_returns_on_db_exception():
    with patch("src.services.scheduler.get_weather", return_value=MOCK_WEATHER), \
         patch("src.services.scheduler.predict_full", return_value=150.0), \
         patch("src.services.scheduler.wh_to_cost", return_value=(0.15, 10.2)), \
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
    with patch("src.services.scheduler.get_weather", return_value=MOCK_WEATHER), \
         patch("src.services.scheduler.predict_full", return_value=150.0), \
         patch("src.services.scheduler.wh_to_cost", return_value=(0.15, 10.2)), \
         patch("src.services.scheduler.insert_prediction"), \
         patch("src.services.scheduler.monitor_reading", return_value={"low_confidence": False}):
        submit_smart_home_reading()
    assert scheduler_module._clean_reading_count == 1


def test_scheduler_does_not_increment_count_on_anomalous_tick():
    scheduler_module._clean_reading_count = 0
    with patch("src.services.scheduler.get_weather", return_value=MOCK_WEATHER), \
         patch("src.services.scheduler.predict_full", return_value=150.0), \
         patch("src.services.scheduler.wh_to_cost", return_value=(0.15, 10.2)), \
         patch("src.services.scheduler.insert_prediction"), \
         patch("src.services.scheduler.monitor_reading", return_value={"low_confidence": True}):
        submit_smart_home_reading()
    assert scheduler_module._clean_reading_count == 0


def test_scheduler_triggers_drift_check_at_100_and_resets_counter():
    scheduler_module._clean_reading_count = 99
    mock_clean_rows = [{"T1": 20.0, "lights": 0} for _ in range(100)]
    drift_result = {"drift_detected": False, "drifted_features": [], "deviations": {}}
    with patch("src.services.scheduler.get_weather", return_value=MOCK_WEATHER), \
         patch("src.services.scheduler.predict_full", return_value=150.0), \
         patch("src.services.scheduler.wh_to_cost", return_value=(0.15, 10.2)), \
         patch("src.services.scheduler.insert_prediction"), \
         patch("src.services.scheduler.monitor_reading", return_value={"low_confidence": False}), \
         patch("src.services.scheduler.get_last_n_clean_readings", return_value=mock_clean_rows) as mock_fetch, \
         patch("src.services.scheduler.check_drift", return_value=drift_result) as mock_drift, \
         patch("src.services.scheduler.store_drift_event") as mock_store:
        submit_smart_home_reading()
    mock_drift.assert_called_once_with(mock_clean_rows)
    mock_store.assert_called_once()
    assert scheduler_module._clean_reading_count == 0


def test_scheduler_does_not_trigger_drift_check_below_100():
    scheduler_module._clean_reading_count = 50
    with patch("src.services.scheduler.get_weather", return_value=MOCK_WEATHER), \
         patch("src.services.scheduler.predict_full", return_value=150.0), \
         patch("src.services.scheduler.wh_to_cost", return_value=(0.15, 10.2)), \
         patch("src.services.scheduler.insert_prediction"), \
         patch("src.services.scheduler.monitor_reading", return_value={"low_confidence": False}), \
         patch("src.services.scheduler.check_drift") as mock_drift, \
         patch("src.services.scheduler.store_drift_event") as mock_store:
        submit_smart_home_reading()
    mock_drift.assert_not_called()
    mock_store.assert_not_called()
    assert scheduler_module._clean_reading_count == 51


def test_scheduler_resets_counter_and_skips_drift_check_on_fetch_failure():
    scheduler_module._clean_reading_count = 99
    with patch("src.services.scheduler.get_weather", return_value=MOCK_WEATHER), \
         patch("src.services.scheduler.predict_full", return_value=150.0), \
         patch("src.services.scheduler.wh_to_cost", return_value=(0.15, 10.2)), \
         patch("src.services.scheduler.insert_prediction"), \
         patch("src.services.scheduler.monitor_reading", return_value={"low_confidence": False}), \
         patch("src.services.scheduler.get_last_n_clean_readings", side_effect=Exception("connection timeout")), \
         patch("src.services.scheduler.check_drift") as mock_drift, \
         patch("src.services.scheduler.store_drift_event") as mock_store:
        submit_smart_home_reading()
    mock_drift.assert_not_called()
    mock_store.assert_not_called()
    assert scheduler_module._clean_reading_count == 0
