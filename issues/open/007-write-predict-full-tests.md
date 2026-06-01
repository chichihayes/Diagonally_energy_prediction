---
id: "007"
slug: write-predict-full-tests
feature: F1
epic: E2
title: Write tests for POST /api/v1/predict/full
status: open
---

# 007 — Write tests for POST /api/v1/predict/full

## Goal

`POST /api/v1/predict/full` has a full test suite that verifies the success
path, field validation, weather failure propagation, and Supabase insert call —
so that regressions are caught by CI before they reach production.

## User Story

As a developer maintaining the Smart Home tier, I want automated tests for
`POST /api/v1/predict/full` so that any regression in inference, cost
calculation, or database storage is caught by CI before it reaches production.

## Reference Docs

- `docs/api-contracts.md` — POST /api/v1/predict/full expected request, response, and error codes
- `docs/schema.md` — predictions table schema (tier, predicted_wh, predicted_kwh, estimated_cost_ngn, location)

## Acceptance Criteria

- [ ] Valid 19-field body + `location` returns HTTP 200 with `predicted_wh`, `predicted_kwh`, `estimated_cost_ngn`
- [ ] `predicted_kwh == predicted_wh / 1000` is asserted in a dedicated test
- [ ] `estimated_cost_ngn == round(predicted_kwh * tariff, 2)` is asserted in a dedicated test
- [ ] Omitting any single sensor field (e.g. `T3`) returns HTTP 422
- [ ] If `get_weather` raises `HTTPException(500)`, the endpoint returns 500
- [ ] `insert_prediction` is called exactly once per request, with `tier="full"` and correct `location`
- [ ] All tests pass without a real model file, real Supabase credentials, or a live weather API call

## Files to Modify

- `tests/test_api.py` — add all six tests listed in the implementation plan

## Out of Scope

- Unit tests for `predict_full`, `assemble_full_features` (covered in issue 006)
- Unit tests for `train_full.py` or `build_full_matrix` (covered in issue 005)
- Tests for `/api/v1/predict/simple` or any other route
- Frontend tests

## Implementation Plan

### Step 1 — test fixtures and valid body constant

No production code change. Add to `tests/test_api.py`:

```python
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient

_VALID_FULL_BODY = {
    "lights": 0,
    "T1": 19.89, "RH_1": 47.6,
    "T2": 19.2,  "RH_2": 44.79,
    "T3": 19.79, "RH_3": 44.73,
    "T4": 17.17, "RH_4": 41.67,
    "T5": 17.2,  "RH_5": 55.2,
    "T6": 7.03,  "RH_6": 84.26,
    "T7": 17.2,  "RH_7": 41.63,
    "T8": 18.2,  "RH_8": 48.9,
    "T9": 17.03, "RH_9": 45.53,
    "location": "Lagos",
}

_MOCK_WEATHER = {
    "T_out": 6.6, "Press_mm_hg": 733.5, "RH_out": 92.0,
    "Windspeed": 7.0, "Visibility": 63.0, "Tdewpoint": 5.3,
}
```

---

### Step 2 — success path: 200 response with all three fields

**Test** (`tests/test_api.py`):
```python
def test_predict_full_valid_body_returns_200_with_all_fields():
    from src.api.main import app
    client = TestClient(app)
    with patch("src.api.routes.get_weather", return_value=_MOCK_WEATHER), \
         patch("src.api.routes.predict_full", return_value=84.3), \
         patch("src.api.routes.insert_prediction"), \
         patch.dict("os.environ", {"ELECTRICITY_TARIFF_NGN_PER_KWH": "68.00"}):
        response = client.post("/api/v1/predict/full", json=_VALID_FULL_BODY)
    assert response.status_code == 200
    data = response.json()
    assert set(data.keys()) == {"predicted_wh", "predicted_kwh", "estimated_cost_ngn"}
    assert data["predicted_wh"] == pytest.approx(84.3)
```

---

### Step 3 — cost math: kwh and ngn derivations

**Test** (`tests/test_api.py`):
```python
def test_predict_full_predicted_kwh_equals_wh_over_1000():
    from src.api.main import app
    client = TestClient(app)
    with patch("src.api.routes.get_weather", return_value=_MOCK_WEATHER), \
         patch("src.api.routes.predict_full", return_value=84.3), \
         patch("src.api.routes.insert_prediction"), \
         patch.dict("os.environ", {"ELECTRICITY_TARIFF_NGN_PER_KWH": "68.00"}):
        response = client.post("/api/v1/predict/full", json=_VALID_FULL_BODY)
    data = response.json()
    assert data["predicted_kwh"] == pytest.approx(data["predicted_wh"] / 1000, rel=1e-5)

def test_predict_full_estimated_cost_ngn_matches_tariff():
    from src.api.main import app
    client = TestClient(app)
    with patch("src.api.routes.get_weather", return_value=_MOCK_WEATHER), \
         patch("src.api.routes.predict_full", return_value=84.3), \
         patch("src.api.routes.insert_prediction"), \
         patch.dict("os.environ", {"ELECTRICITY_TARIFF_NGN_PER_KWH": "68.00"}):
        response = client.post("/api/v1/predict/full", json=_VALID_FULL_BODY)
    data = response.json()
    assert data["estimated_cost_ngn"] == round(data["predicted_kwh"] * 68.00, 2)
```

---

### Step 4 — validation: missing sensor field returns 422

**Test** (`tests/test_api.py`):
```python
def test_predict_full_missing_sensor_field_returns_422():
    from src.api.main import app
    client = TestClient(app)
    body = {k: v for k, v in _VALID_FULL_BODY.items() if k != "T3"}
    response = client.post("/api/v1/predict/full", json=body)
    assert response.status_code == 422
```

---

### Step 5 — weather failure propagates 500

**Test** (`tests/test_api.py`):
```python
def test_predict_full_weather_failure_returns_500():
    from fastapi import HTTPException
    from src.api.main import app
    client = TestClient(app)
    with patch("src.api.routes.get_weather", side_effect=HTTPException(status_code=500, detail="weather unavailable")), \
         patch("src.api.routes.predict_full", return_value=84.3), \
         patch("src.api.routes.insert_prediction"):
        response = client.post("/api/v1/predict/full", json=_VALID_FULL_BODY)
    assert response.status_code == 500
```

---

### Step 6 — Supabase insert called once with correct fields

**Test** (`tests/test_api.py`):
```python
def test_predict_full_calls_insert_prediction_once_with_tier_full():
    from src.api.main import app
    client = TestClient(app)
    with patch("src.api.routes.get_weather", return_value=_MOCK_WEATHER), \
         patch("src.api.routes.predict_full", return_value=84.3), \
         patch("src.api.routes.insert_prediction") as mock_insert, \
         patch.dict("os.environ", {"ELECTRICITY_TARIFF_NGN_PER_KWH": "68.00"}):
        client.post("/api/v1/predict/full", json=_VALID_FULL_BODY)
    mock_insert.assert_called_once()
    row = mock_insert.call_args[0][0]
    assert row["tier"] == "full"
    assert row["location"] == "Lagos"
    assert row["predicted_wh"] == pytest.approx(84.3)
```

## Git

- **Branch:** `feat/007-predict-full-tests`
- **Commit format:** `test(api): add full test suite for POST /api/v1/predict/full`
- **PR title:** `test(api): test suite for POST /api/v1/predict/full`
