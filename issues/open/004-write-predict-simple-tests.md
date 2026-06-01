---
id: "004"
slug: write-predict-simple-tests
feature: F1
epic: E1
title: Write integration tests for POST /api/v1/predict/simple and weather caching
status: open
---

# 004 — Write integration tests for POST /api/v1/predict/simple and weather caching

## Goal

The test suite covers the full happy path, all error branches, and the weather
cache behaviour for F1 so that CI catches regressions on the Basic tier endpoint
without requiring a live model or network connection.

## User Story

As a developer merging changes to the Basic tier, I want a test suite that catches
regressions in the predict/simple endpoint and weather caching so I can ship with
confidence that the contract has not broken.

## Reference Docs

- `docs/api-contracts.md` — POST /api/v1/predict/simple request/response shape and error codes
- `CLAUDE.md` — TDD rules: failing test first, assertions must name function + input + expected output
- `CLAUDE.md` — error handling: 422 for validation failure, 500 for weather failure

## Acceptance Criteria

- [ ] `test_predict_simple_valid_input_returns_200` passes — verifies status code and all four response keys
- [ ] `test_predict_simple_missing_field_returns_422` passes — omitting `T1` yields 422
- [ ] `test_predict_simple_unknown_city_returns_500` passes — weather raises 500 when city not found
- [ ] `test_weather_cache_hit_skips_second_request` passes — two calls within TTL produce one HTTP request
- [ ] `test_weather_cache_miss_after_ttl_makes_new_request` passes — call after TTL expiry produces a new HTTP request
- [ ] All tests use mocks for OpenWeatherMap, Supabase, and the model — no live network calls
- [ ] All tests run in `pytest` without extra environment configuration beyond `monkeypatch`

## Files to Modify

- `tests/test_api.py` — add three endpoint tests
- `tests/test_weather.py` — add two cache behaviour tests (cache hit and cache miss/expiry)

## Out of Scope

- Tests for model training, feature assembly, cost calculation, or database insert (those belong to their own test files per issues 001–003)
- Tests for `POST /api/v1/predict/full` or any forecast endpoint
- Performance benchmarks

## Implementation Plan

### Step 1 — write test_api.py endpoint tests (all three must fail before route exists)

**File:** `tests/test_api.py`

```python
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from fastapi import HTTPException

MOCK_WEATHER = {
    "T_out": 28.4, "RH_out": 82.0,
    "Windspeed": 3.1, "Visibility": 10.0, "Tdewpoint": 25.1,
}

@pytest.fixture
def client():
    from src.api.main import app
    return TestClient(app)

def test_predict_simple_valid_input_returns_200(client):
    with patch("src.api.routes.get_weather", return_value=MOCK_WEATHER), \
         patch("src.api.routes.predict_simple", return_value=60.5), \
         patch("src.api.routes.insert_prediction"):
        resp = client.post("/api/v1/predict/simple", json={
            "lights": 0, "T1": 19.89, "location": "Lagos"
        })
    assert resp.status_code == 200
    body = resp.json()
    assert "predicted_wh" in body
    assert "predicted_kwh" in body
    assert "estimated_cost_ngn" in body
    assert "weather_factors" in body
    assert body["predicted_wh"] == pytest.approx(60.5)
    assert body["predicted_kwh"] == pytest.approx(0.0605)
    assert body["weather_factors"] == MOCK_WEATHER

def test_predict_simple_missing_field_returns_422(client):
    resp = client.post("/api/v1/predict/simple", json={
        "lights": 0, "location": "Lagos"
        # T1 intentionally omitted
    })
    assert resp.status_code == 422

def test_predict_simple_unknown_city_returns_500(client):
    with patch("src.api.routes.get_weather",
               side_effect=HTTPException(status_code=500, detail="Weather fetch failed")):
        resp = client.post("/api/v1/predict/simple", json={
            "lights": 0, "T1": 19.89, "location": "UnknownXYZ"
        })
    assert resp.status_code == 500
```

Confirm all three tests fail before `src/api/routes.py` and `src/api/main.py` are implemented (issue 003).

---

### Step 2 — write test_weather.py cache tests (both must fail before weather.py cache logic exists)

**File:** `tests/test_weather.py`

```python
import time, pytest
from unittest.mock import patch, MagicMock
from fastapi import HTTPException

MOCK_OWM_RESPONSE = {
    "main": {"temp": 28.4, "humidity": 82.0, "temp_min": 25.1},
    "wind": {"speed": 3.1},
    "visibility": 10000,
}

def _make_mock(status_code=200, json_data=MOCK_OWM_RESPONSE):
    m = MagicMock()
    m.status_code = status_code
    m.json.return_value = json_data
    return m

def test_weather_cache_hit_skips_second_request():
    """Two get_weather calls within TTL produce exactly one HTTP request."""
    from src.services.weather import get_weather
    with patch("src.services.weather._cache", {}), \
         patch("requests.get", return_value=_make_mock()) as mock_get:
        get_weather("Lagos")
        get_weather("Lagos")
    assert mock_get.call_count == 1

def test_weather_cache_miss_after_ttl_makes_new_request(monkeypatch):
    """A call after TTL expiry bypasses the cache and makes a fresh HTTP request."""
    monkeypatch.setattr("src.services.weather._CACHE_TTL", 0)  # expire immediately
    from src.services.weather import get_weather
    with patch("src.services.weather._cache", {}), \
         patch("requests.get", return_value=_make_mock()) as mock_get:
        get_weather("Lagos")
        time.sleep(0.01)  # let the 0-second TTL expire
        get_weather("Lagos")
    assert mock_get.call_count == 2

def test_get_weather_returns_expected_keys():
    from src.services.weather import get_weather
    with patch("src.services.weather._cache", {}), \
         patch("requests.get", return_value=_make_mock()):
        result = get_weather("Lagos")
    assert set(result.keys()) == {"T_out", "RH_out", "Windspeed", "Visibility", "Tdewpoint"}
    assert all(isinstance(v, float) for v in result.values())

def test_get_weather_raises_500_on_bad_status():
    from src.services.weather import get_weather
    with patch("src.services.weather._cache", {}), \
         patch("requests.get", return_value=_make_mock(status_code=401)):
        with pytest.raises(HTTPException) as exc:
            get_weather("Lagos")
    assert exc.value.status_code == 500

def test_get_weather_raises_500_on_network_error():
    import requests as req_lib
    from src.services.weather import get_weather
    with patch("src.services.weather._cache", {}), \
         patch("requests.get", side_effect=req_lib.RequestException("timeout")):
        with pytest.raises(HTTPException) as exc:
            get_weather("Lagos")
    assert exc.value.status_code == 500
```

Confirm both cache tests fail before `weather.py` TTL cache logic is implemented (issue 002).

---

### Step 3 — confirm all tests pass together

After issues 001–003 are merged:

```bash
pytest tests/test_api.py tests/test_weather.py -v
```

Expected: 8 tests passing, 0 failing, 0 errors.

## Git

- **Branch:** `test/004-predict-simple-tests`
- **Commit format:** `test(api,weather): add endpoint integration tests and weather cache behaviour tests for F1`
- **PR title:** `test: add predict/simple endpoint and weather cache tests`
