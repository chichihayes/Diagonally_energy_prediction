---
id: "011"
slug: write-forecast-7d-tests
feature: F2
epic: E3
title: Write tests for GET /api/v1/forecast/7d and project_monthly_bill
status: open
---

# 011 — Write tests for GET /api/v1/forecast/7d and `project_monthly_bill`

## Goal

`GET /api/v1/forecast/7d` and `project_monthly_bill` each have a test suite
that verifies the success path, response shape, bill ordering invariant, and
error propagation — so regressions in the forecast pipeline are caught by CI
before they reach production.

## User Story

As a developer maintaining the forecast feature, I want automated tests for
the 7-day endpoint and bill projection function so that any regression in
forecast formatting, cost calculation, or error handling is caught by CI.

## Reference Docs

- `docs/api-contracts.md` — GET /api/v1/forecast/7d response shape, error codes
- `docs/schema.md` — Forecast Output Schema (projected_month_bill fields)
- `CLAUDE.md` — Layer 3 Bill Estimation conventions (rounding, env var)

## Acceptance Criteria

- [ ] `test_forecast_7d_valid_location_returns_200_with_7_element_array` — response has HTTP 200, `forecast` list has 7 items
- [ ] `test_forecast_7d_bill_fields_all_present` — `projected_month_bill` contains `optimistic_ngn`, `most_likely_ngn`, `pessimistic_ngn`
- [ ] `test_forecast_7d_bill_ordering_holds` — `optimistic_ngn <= most_likely_ngn <= pessimistic_ngn`
- [ ] `test_forecast_7d_missing_location_returns_400`
- [ ] `test_forecast_7d_model_error_returns_500`
- [ ] `test_project_monthly_bill_optimistic_uses_lower_wh` — correct NGN value computed from `lower_wh` inputs
- [ ] `test_project_monthly_bill_most_likely_uses_predicted_wh` — correct NGN value computed from `predicted_wh` inputs
- [ ] `test_project_monthly_bill_pessimistic_uses_upper_wh` — correct NGN value computed from `upper_wh` inputs
- [ ] All tests pass without a real model file, real Supabase connection, or live weather API call

## Files to Modify

- `tests/test_api.py` — add 5 tests for GET /api/v1/forecast/7d
- `tests/test_cost.py` — add 3 tests for `project_monthly_bill`

## Out of Scope

- Unit tests for `forecast_7d` internals (covered in issue 008)
- Frontend tests
- Tests for other routes (predict/full, predict/simple, forecast/24h)

## Implementation Plan

### Step 1 — shared fixtures and constants (no production code change)

Add to `tests/test_api.py`:

```python
_MOCK_7D_FORECAST = [
    {
        "date": f"2026-06-0{i+1}",
        "predicted_wh": 6000.0 + i * 200,
        "predicted_kwh": round((6000.0 + i * 200) / 1000, 6),
        "lower_wh": 4000.0 + i * 200,
        "upper_wh": 8000.0 + i * 200,
        "estimated_cost_ngn": round((6000.0 + i * 200) / 1000 * 68.00, 2),
    }
    for i in range(7)
]

_MOCK_FORECAST_7D_RESULT = {
    "forecast": _MOCK_7D_FORECAST,
    "peak_day": "Sunday",
    "lowest_day": "Monday",
}

_MOCK_BILL = {
    "optimistic_ngn": 3200.00,
    "most_likely_ngn": 4200.00,
    "pessimistic_ngn": 5100.00,
}
```

Add to `tests/test_cost.py`:

```python
_COST_MOCK_FORECAST = [
    {"predicted_wh": 6000.0, "lower_wh": 4000.0, "upper_wh": 8000.0},
    {"predicted_wh": 6000.0, "lower_wh": 4000.0, "upper_wh": 8000.0},
    {"predicted_wh": 6000.0, "lower_wh": 4000.0, "upper_wh": 8000.0},
    {"predicted_wh": 6000.0, "lower_wh": 4000.0, "upper_wh": 8000.0},
    {"predicted_wh": 6000.0, "lower_wh": 4000.0, "upper_wh": 8000.0},
    {"predicted_wh": 6000.0, "lower_wh": 4000.0, "upper_wh": 8000.0},
    {"predicted_wh": 6000.0, "lower_wh": 4000.0, "upper_wh": 8000.0},
]
# All rows identical for easy hand-calculation:
# sum(lower_wh)  = 7 * 4000 = 28000 Wh = 28 kWh  →  28 * (30/7) * 68 = 8160.00
# sum(predicted) = 7 * 6000 = 42000 Wh = 42 kWh  →  42 * (30/7) * 68 = 12240.00
# sum(upper_wh)  = 7 * 8000 = 56000 Wh = 56 kWh  →  56 * (30/7) * 68 = 16320.00
```

---

### Step 2 — test: valid location returns 200 with 7-element array

**Test** (`tests/test_api.py`):
```python
def test_forecast_7d_valid_location_returns_200_with_7_element_array():
    from src.api.main import app
    from fastapi.testclient import TestClient
    from unittest.mock import patch
    client = TestClient(app)
    with patch("src.api.routes.forecast_7d", return_value=_MOCK_FORECAST_7D_RESULT), \
         patch("src.api.routes.project_monthly_bill", return_value=_MOCK_BILL):
        response = client.get("/api/v1/forecast/7d?location=Lagos")
    assert response.status_code == 200
    assert len(response.json()["forecast"]) == 7
```

---

### Step 3 — test: all three bill fields present

**Test** (`tests/test_api.py`):
```python
def test_forecast_7d_bill_fields_all_present():
    from src.api.main import app
    from fastapi.testclient import TestClient
    from unittest.mock import patch
    client = TestClient(app)
    with patch("src.api.routes.forecast_7d", return_value=_MOCK_FORECAST_7D_RESULT), \
         patch("src.api.routes.project_monthly_bill", return_value=_MOCK_BILL):
        response = client.get("/api/v1/forecast/7d?location=Lagos")
    bill = response.json()["projected_month_bill"]
    assert {"optimistic_ngn", "most_likely_ngn", "pessimistic_ngn"}.issubset(bill.keys())
```

---

### Step 4 — test: bill ordering invariant holds

**Test** (`tests/test_api.py`):
```python
def test_forecast_7d_bill_ordering_holds():
    from src.api.main import app
    from fastapi.testclient import TestClient
    from unittest.mock import patch
    client = TestClient(app)
    with patch("src.api.routes.forecast_7d", return_value=_MOCK_FORECAST_7D_RESULT), \
         patch("src.api.routes.project_monthly_bill", return_value=_MOCK_BILL):
        response = client.get("/api/v1/forecast/7d?location=Lagos")
    bill = response.json()["projected_month_bill"]
    assert bill["optimistic_ngn"] <= bill["most_likely_ngn"] <= bill["pessimistic_ngn"]
```

---

### Step 5 — test: missing location returns 400

**Test** (`tests/test_api.py`):
```python
def test_forecast_7d_missing_location_returns_400():
    from src.api.main import app
    from fastapi.testclient import TestClient
    client = TestClient(app)
    response = client.get("/api/v1/forecast/7d")
    assert response.status_code == 400
```

---

### Step 6 — test: model error returns 500

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

---

### Step 7 — test: project_monthly_bill optimistic uses lower_wh

**Test** (`tests/test_cost.py`):
```python
def test_project_monthly_bill_optimistic_uses_lower_wh():
    import pytest
    from unittest.mock import patch
    from src.services.cost import project_monthly_bill
    with patch.dict("os.environ", {"ELECTRICITY_TARIFF_NGN_PER_KWH": "68.00"}):
        result = project_monthly_bill(_COST_MOCK_FORECAST)
    assert result["optimistic_ngn"] == pytest.approx(8160.00, abs=0.01)
```

---

### Step 8 — test: project_monthly_bill most_likely uses predicted_wh

**Test** (`tests/test_cost.py`):
```python
def test_project_monthly_bill_most_likely_uses_predicted_wh():
    import pytest
    from unittest.mock import patch
    from src.services.cost import project_monthly_bill
    with patch.dict("os.environ", {"ELECTRICITY_TARIFF_NGN_PER_KWH": "68.00"}):
        result = project_monthly_bill(_COST_MOCK_FORECAST)
    assert result["most_likely_ngn"] == pytest.approx(12240.00, abs=0.01)
```

---

### Step 9 — test: project_monthly_bill pessimistic uses upper_wh

**Test** (`tests/test_cost.py`):
```python
def test_project_monthly_bill_pessimistic_uses_upper_wh():
    import pytest
    from unittest.mock import patch
    from src.services.cost import project_monthly_bill
    with patch.dict("os.environ", {"ELECTRICITY_TARIFF_NGN_PER_KWH": "68.00"}):
        result = project_monthly_bill(_COST_MOCK_FORECAST)
    assert result["pessimistic_ngn"] == pytest.approx(16320.00, abs=0.01)
```

Run all eight tests — all must pass before marking this issue done.

---

## Git

- **Branch:** `feat/011-forecast-7d-tests`
- **Commit format:** `test(api,cost): add test suite for GET /api/v1/forecast/7d and project_monthly_bill`
- **PR title:** `test(api,cost): full test suite for 7-day forecast endpoint and bill projection`
