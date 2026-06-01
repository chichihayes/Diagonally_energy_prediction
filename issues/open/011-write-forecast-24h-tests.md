---
id: "011"
slug: write-forecast-24h-tests
feature: F1
epic: E3
title: Write tests for GET /api/v1/forecast/24h
status: open
---

# 011 — Write tests for GET /api/v1/forecast/24h

## Goal

`tests/test_api.py` has 7 passing test functions that verify the 24h forecast
endpoint returns the correct response shape, correct peak/lowest detection,
and correct error codes — all against a mocked `forecast_24h` so no model file
or weather API is needed in CI.

## User Story

As a developer on this project, I want automated tests for
`GET /api/v1/forecast/24h` so that regressions in the forecast endpoint are
caught by CI on every push to main before any code is merged.

## Reference Docs

- `docs/api-contracts.md` — GET /api/v1/forecast/24h: expected response shape, error codes
- `CLAUDE.md` — TDD rules: write the failing test first, confirm it fails, then implement; every transformed value has a specific assertion

## Acceptance Criteria

- [ ] `test_forecast_24h_valid_location_returns_200` passes — `GET /api/v1/forecast/24h?location=Lagos` returns 200
- [ ] `test_forecast_24h_forecast_array_has_24_elements` passes — `response.json()["forecast"]` has exactly 24 items
- [ ] `test_forecast_24h_each_item_has_required_fields` passes — every item contains all 6 required keys: `hour, predicted_wh, predicted_kwh, lower_wh, upper_wh, estimated_cost_ngn`
- [ ] `test_forecast_24h_peak_hour_is_highest_predicted_wh` passes — `peak_hour` equals the `hour` of the item with the highest `predicted_wh`
- [ ] `test_forecast_24h_lowest_hour_is_lowest_predicted_wh` passes — `lowest_hour` equals the `hour` of the item with the lowest `predicted_wh`
- [ ] `test_forecast_24h_missing_location_returns_400` passes — `GET /api/v1/forecast/24h` (no location) returns 400
- [ ] `test_forecast_24h_model_error_returns_500` passes — when `forecast_24h` raises `RuntimeError`, endpoint returns 500
- [ ] All 7 tests are written BEFORE issue 010 is merged — they must fail first against the route-less codebase

## Files to Modify

- `tests/test_api.py` — add 7 test functions

> Do not modify `forecast.py`, `routes.py`, or any other file. This issue is tests only.

## Out of Scope

- Unit tests for `forecast_24h()` in `forecast.py` (covered in issue 009)
- Unit tests for `build_lag_matrix` or `select_best_by_mape` (covered in issue 008)
- Tests for 7-day forecast (F2)
- Tests for forecast.html (F3)

## Implementation Plan

### Step 1 — Build the shared mock fixture and add 7 test functions to test_api.py

`forecast_24h` is patched at `src.api.routes.forecast_24h` so the route under
test calls the mock instead of loading `model_forecast.joblib`.

The mock returns 24 dicts with varying `yhat` values (100 + h * 10 for hour h)
so peak and lowest detection can be verified deterministically.

**Confirm tests fail** by running `pytest tests/test_api.py -k forecast_24h` before
issue 010 is implemented — all 7 tests must fail or error (route does not exist yet).

**File:** `tests/test_api.py` — add:

```python
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from src.api.main import app

client = TestClient(app)

# 24 entries: hour 0 → yhat=100, hour 23 → yhat=330
# peak = hour 23, lowest = hour 0
_MOCK_FORECAST_24H = [
    {
        "ds": f"2026-06-01T{h:02d}:00:00Z",
        "yhat": float(100 + h * 10),
        "yhat_lower": float(80 + h * 10),
        "yhat_upper": float(120 + h * 10),
        "predicted_kwh": round((100 + h * 10) / 1000, 3),
        "estimated_cost_ngn": round((100 + h * 10) / 1000 * 68.0, 2),
    }
    for h in range(24)
]


@pytest.fixture
def mock_forecast_24h():
    with patch("src.api.routes.forecast_24h", return_value=_MOCK_FORECAST_24H) as m:
        yield m


def test_forecast_24h_valid_location_returns_200(mock_forecast_24h):
    resp = client.get("/api/v1/forecast/24h?location=Lagos")
    assert resp.status_code == 200


def test_forecast_24h_forecast_array_has_24_elements(mock_forecast_24h):
    resp = client.get("/api/v1/forecast/24h?location=Lagos")
    assert len(resp.json()["forecast"]) == 24


def test_forecast_24h_each_item_has_required_fields(mock_forecast_24h):
    resp = client.get("/api/v1/forecast/24h?location=Lagos")
    required = {"hour", "predicted_wh", "predicted_kwh", "lower_wh", "upper_wh", "estimated_cost_ngn"}
    for item in resp.json()["forecast"]:
        assert set(item.keys()) == required


def test_forecast_24h_peak_hour_is_highest_predicted_wh(mock_forecast_24h):
    resp = client.get("/api/v1/forecast/24h?location=Lagos")
    data = resp.json()
    max_item = max(data["forecast"], key=lambda x: x["predicted_wh"])
    assert data["peak_hour"] == max_item["hour"]


def test_forecast_24h_lowest_hour_is_lowest_predicted_wh(mock_forecast_24h):
    resp = client.get("/api/v1/forecast/24h?location=Lagos")
    data = resp.json()
    min_item = min(data["forecast"], key=lambda x: x["predicted_wh"])
    assert data["lowest_hour"] == min_item["hour"]


def test_forecast_24h_missing_location_returns_400():
    resp = client.get("/api/v1/forecast/24h")
    assert resp.status_code == 400


def test_forecast_24h_model_error_returns_500():
    with patch("src.api.routes.forecast_24h", side_effect=RuntimeError("model failed")):
        resp = client.get("/api/v1/forecast/24h?location=Lagos")
        assert resp.status_code == 500
```

## Git

- **Branch:** `feat/011-write-forecast-24h-tests`
- **Commit format:** `test(api): add 7 tests for GET /api/v1/forecast/24h`
- **PR title:** `test(api): write tests for 24h forecast endpoint`
