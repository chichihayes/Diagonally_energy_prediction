---
id: "010"
slug: implement-forecast-7d-route
feature: F2
epic: E3
title: Implement GET /api/v1/forecast/7d route
status: open
---

# 010 — Implement GET /api/v1/forecast/7d route

## Goal

`GET /api/v1/forecast/7d?location=Lagos` returns a single JSON response
containing the 7-day daily forecast array, peak_day, lowest_day, and the
three-value monthly bill projection — so the frontend has everything it needs
in one call.

## User Story

As a homeowner planning ahead, I want to call one endpoint and receive my
full 7-day outlook plus projected monthly bill in a single response so I
can see both without making multiple requests.

## Reference Docs

- `docs/api-contracts.md` — GET /api/v1/forecast/7d — request params, full
  response shape, error codes
- `docs/architecture.md` — service boundaries: routes.py calls forecast.py
  and cost.py; neither module calls the other directly

## Acceptance Criteria

- [ ] `GET /api/v1/forecast/7d?location=Lagos` returns HTTP 200
- [ ] Response body contains top-level keys: `forecast`, `peak_day`, `lowest_day`, `projected_month_bill`
- [ ] `forecast` is a list of 7 dicts, each with `date`, `predicted_wh`, `predicted_kwh`, `lower_wh`, `upper_wh`, `estimated_cost_ngn`
- [ ] `projected_month_bill` contains `optimistic_ngn`, `most_likely_ngn`, `pessimistic_ngn`
- [ ] Calling without `?location=` returns HTTP 400
- [ ] If `forecast_7d()` raises any exception, the route returns HTTP 500
- [ ] `location` query param is accepted but **not** passed to `forecast_7d()` — the forecast model does not use it
- [ ] Route depends on: `forecast_7d` from `src/model/forecast.py` and `project_monthly_bill` from `src/services/cost.py`

## Files to Modify

- `src/api/routes.py` — add `GET /api/v1/forecast/7d` route after the existing forecast/24h route

## Out of Scope

- `forecast_7d` implementation (issue 008)
- `project_monthly_bill` implementation (issue 009)
- forecast.html frontend (F3)
- Model leaderboard route (F4)
- Persisting forecast results to Supabase (not in scope for F2)

## Implementation Plan

### Step 1 — failing test: route exists and returns 200

**Test** (`tests/test_api.py`):
```python
def test_forecast_7d_valid_location_returns_200():
    from src.api.main import app
    from fastapi.testclient import TestClient
    client = TestClient(app)
    mock_forecast_result = {
        "forecast": [
            {
                "date": "2026-06-01",
                "predicted_wh": 6000.0,
                "predicted_kwh": 6.0,
                "lower_wh": 4000.0,
                "upper_wh": 8000.0,
                "estimated_cost_ngn": 408.0,
            }
        ] * 7,
        "peak_day": "Monday",
        "lowest_day": "Sunday",
    }
    mock_bill = {
        "optimistic_ngn": 3200.0,
        "most_likely_ngn": 4200.0,
        "pessimistic_ngn": 5100.0,
    }
    from unittest.mock import patch
    with patch("src.api.routes.forecast_7d", return_value=mock_forecast_result), \
         patch("src.api.routes.project_monthly_bill", return_value=mock_bill):
        response = client.get("/api/v1/forecast/7d?location=Lagos")
    assert response.status_code == 200
```

Confirm it fails (`404` — route does not exist yet).

---

### Step 2 — failing test: response body contains all required top-level keys

**Test** (`tests/test_api.py`):
```python
def test_forecast_7d_response_has_required_keys():
    from src.api.main import app
    from fastapi.testclient import TestClient
    from unittest.mock import patch
    client = TestClient(app)
    mock_forecast_result = {
        "forecast": [
            {
                "date": "2026-06-01",
                "predicted_wh": 6000.0,
                "predicted_kwh": 6.0,
                "lower_wh": 4000.0,
                "upper_wh": 8000.0,
                "estimated_cost_ngn": 408.0,
            }
        ] * 7,
        "peak_day": "Monday",
        "lowest_day": "Sunday",
    }
    mock_bill = {
        "optimistic_ngn": 3200.0,
        "most_likely_ngn": 4200.0,
        "pessimistic_ngn": 5100.0,
    }
    with patch("src.api.routes.forecast_7d", return_value=mock_forecast_result), \
         patch("src.api.routes.project_monthly_bill", return_value=mock_bill):
        response = client.get("/api/v1/forecast/7d?location=Lagos")
    data = response.json()
    assert set(data.keys()) == {"forecast", "peak_day", "lowest_day", "projected_month_bill"}
    assert len(data["forecast"]) == 7
    assert set(data["projected_month_bill"].keys()) == {
        "optimistic_ngn", "most_likely_ngn", "pessimistic_ngn"
    }
```

Confirm it fails.

---

### Step 3 — failing test: missing location returns 400

**Test** (`tests/test_api.py`):
```python
def test_forecast_7d_missing_location_returns_400():
    from src.api.main import app
    from fastapi.testclient import TestClient
    client = TestClient(app)
    response = client.get("/api/v1/forecast/7d")
    assert response.status_code == 400
```

Confirm it fails (currently 404).

---

### Step 4 — failing test: forecast model error returns 500

**Test** (`tests/test_api.py`):
```python
def test_forecast_7d_model_error_returns_500():
    from src.api.main import app
    from fastapi.testclient import TestClient
    from unittest.mock import patch
    client = TestClient(app)
    with patch("src.api.routes.forecast_7d", side_effect=Exception("model crashed")):
        response = client.get("/api/v1/forecast/7d?location=Lagos")
    assert response.status_code == 500
```

Confirm it fails.

---

### Step 5 — implement the route in `src/api/routes.py`

Add after the existing forecast/24h route:

```python
from src.model.forecast import forecast_7d
from src.services.cost import project_monthly_bill

@router.get("/forecast/7d")
def get_forecast_7d(location: str = None):
    if not location:
        raise HTTPException(status_code=400, detail="location query param is required")
    try:
        result = forecast_7d()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    bill = project_monthly_bill(result["forecast"])
    return {
        "forecast": result["forecast"],
        "peak_day": result["peak_day"],
        "lowest_day": result["lowest_day"],
        "projected_month_bill": bill,
    }
```

Run all four tests — all must pass.

---

## Git

- **Branch:** `feat/010-forecast-7d-route`
- **Commit format:** `feat(api): add GET /api/v1/forecast/7d route with bill projection`
- **PR title:** `feat(api): GET /api/v1/forecast/7d — 7-day forecast + monthly bill`
