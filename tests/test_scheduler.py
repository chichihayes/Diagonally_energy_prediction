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
