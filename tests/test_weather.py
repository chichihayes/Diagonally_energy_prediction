import os
import time
import pytest
from unittest.mock import patch, MagicMock
from fastapi import HTTPException

_ENV = {"OPENWEATHERMAP_API_KEY": "test_key"}

MOCK_RESPONSE = {
    "main": {"temp": 28.4, "humidity": 82.0, "temp_min": 25.1},
    "wind": {"speed": 3.1},
    "visibility": 10000,
}


def _make_mock(status_code=200, json_data=MOCK_RESPONSE):
    m = MagicMock()
    m.status_code = status_code
    m.json.return_value = json_data
    return m


def test_get_weather_returns_expected_keys():
    from src.services.weather import get_weather
    with patch.dict(os.environ, _ENV):
        with patch("src.services.weather._cache", {}):
            with patch("requests.get", return_value=_make_mock()) as mock_get:
                result = get_weather("Lagos")
    assert set(result.keys()) == {"T_out", "RH_out", "Windspeed", "Visibility", "Tdewpoint"}
    assert all(isinstance(v, float) for v in result.values())


def test_get_weather_caches_response():
    from src.services.weather import get_weather
    with patch.dict(os.environ, _ENV):
        with patch("src.services.weather._cache", {}):
            with patch("requests.get", return_value=_make_mock()) as mock_get:
                get_weather("Lagos")
                get_weather("Lagos")
    assert mock_get.call_count == 1


def test_get_weather_raises_500_on_bad_status():
    from src.services.weather import get_weather
    with patch.dict(os.environ, _ENV):
        with patch("src.services.weather._cache", {}):
            with patch("requests.get", return_value=_make_mock(status_code=401)):
                with pytest.raises(HTTPException) as exc:
                    get_weather("Lagos")
    assert exc.value.status_code == 500


def test_get_weather_raises_500_on_network_error():
    import requests
    from src.services.weather import get_weather
    with patch.dict(os.environ, _ENV):
        with patch("src.services.weather._cache", {}):
            with patch("requests.get", side_effect=requests.RequestException("timeout")):
                with pytest.raises(HTTPException) as exc:
                    get_weather("Lagos")
    assert exc.value.status_code == 500


def test_weather_cache_hit_skips_second_request():
    """Two get_weather calls within TTL produce exactly one HTTP request."""
    from src.services.weather import get_weather
    with patch.dict(os.environ, _ENV), \
         patch("src.services.weather._cache", {}), \
         patch("requests.get", return_value=_make_mock()) as mock_get:
        get_weather("Lagos")
        get_weather("Lagos")
    assert mock_get.call_count == 1


def test_weather_cache_miss_after_ttl_makes_new_request(monkeypatch):
    """A call after TTL expiry bypasses the cache and makes a fresh HTTP request."""
    monkeypatch.setattr("src.services.weather._CACHE_TTL", 0)
    from src.services.weather import get_weather
    with patch.dict(os.environ, _ENV), \
         patch("src.services.weather._cache", {}), \
         patch("requests.get", return_value=_make_mock()) as mock_get:
        get_weather("Lagos")
        time.sleep(0.01)
        get_weather("Lagos")
    assert mock_get.call_count == 2
