---
id: "015"
slug: low-confidence-flag-api
feature: F1
epic: E5
title: Add low_confidence field to prediction API responses
status: open
---

# 015 — Add low_confidence field to prediction API responses

## Goal

Both prediction endpoints call `check_anomaly` before running inference and
always return a `low_confidence` boolean in the response body so homeowners
immediately know when a reading looks unusual.

## User Story

As a homeowner, I want the prediction API to tell me when a result might be
unreliable so I can check whether my sensors are reporting correct values.

## Reference Docs

- `docs/api-contracts.md` — current response shapes for /predict/full and /predict/simple
- `CLAUDE.md` — monitoring conventions: low_confidence flag in response, store anomalous
  readings, prediction still completes even when is_anomaly=True

## Acceptance Criteria

- [ ] `POST /api/v1/predict/full` response always contains `"low_confidence": true` or `"low_confidence": false`
- [ ] `POST /api/v1/predict/simple` response always contains `"low_confidence": true` or `"low_confidence": false`
- [ ] When `check_anomaly` returns `is_anomaly=True`, `store_anomaly` is called once with
  `tier`, `input_features`, `z_scores`, `flagged_features`, and `low_confidence_prediction=True`
- [ ] `store_anomaly` is NOT called when `is_anomaly=False`
- [ ] Prediction and cost calculation complete normally even when `is_anomaly=True`
- [ ] `docs/api-contracts.md` is updated to show `"low_confidence": false` in both response examples

## Files to Modify

- `src/api/routes.py` — import check_anomaly and store_anomaly; call check_anomaly before
  inference; call store_anomaly on anomaly; append low_confidence to response dict
- `docs/api-contracts.md` — add `low_confidence` field to both /predict/full and /predict/simple
  response examples

## Out of Scope

- Frontend display of the low_confidence flag (out of scope per F1 feature spec)
- Email or push alerts for anomalies
- Excluding anomalous readings from clean row pool logic (F2)

**Dependencies:** Issues 013 and 014 must be complete before this issue is started.

## Implementation Plan

### Step 1 — update docs/api-contracts.md

In the `/api/v1/predict/full` 200 response example, add:
```json
"low_confidence": false
```

In the `/api/v1/predict/simple` 200 response example, add:
```json
"low_confidence": false
```

---

### Step 2 — write failing tests

**File:** `tests/test_api.py`

```python
from unittest.mock import patch

MOCK_WEATHER_FULL = {
    "T_out": 28.0, "Press_mm_hg": 733.0, "RH_out": 80.0,
    "Windspeed": 3.0, "Visibility": 10.0, "Tdewpoint": 25.0,
}
MOCK_WEATHER_SIMPLE = {
    "T_out": 28.0, "RH_out": 80.0,
    "Windspeed": 3.0, "Visibility": 10.0, "Tdewpoint": 25.0,
}
FULL_PAYLOAD = {
    "lights": 0, "T1": 20.0, "RH_1": 47.0, "T2": 19.0, "RH_2": 44.0,
    "T3": 19.0, "RH_3": 44.0, "T4": 17.0, "RH_4": 41.0, "T5": 17.0,
    "RH_5": 55.0, "T6": 7.0, "RH_6": 84.0, "T7": 17.0, "RH_7": 41.0,
    "T8": 18.0, "RH_8": 48.0, "T9": 17.0, "RH_9": 45.0, "location": "Lagos",
}
ANOMALY_FALSE = {"is_anomaly": False, "z_scores": {}, "flagged_features": []}
ANOMALY_TRUE  = {"is_anomaly": True,  "z_scores": {"T1": 30.1}, "flagged_features": ["T1"]}

def test_predict_full_response_contains_low_confidence_field(client):
    with patch("src.api.routes.check_anomaly", return_value=ANOMALY_FALSE):
        with patch("src.api.routes.get_weather", return_value=MOCK_WEATHER_FULL):
            resp = client.post("/api/v1/predict/full", json=FULL_PAYLOAD)
    assert resp.status_code == 200
    assert "low_confidence" in resp.json()
    assert resp.json()["low_confidence"] is False

def test_predict_simple_response_contains_low_confidence_field(client):
    with patch("src.api.routes.check_anomaly", return_value=ANOMALY_FALSE):
        with patch("src.api.routes.get_weather", return_value=MOCK_WEATHER_SIMPLE):
            resp = client.post(
                "/api/v1/predict/simple",
                json={"lights": 0, "T1": 20.0, "location": "Lagos"},
            )
    assert resp.status_code == 200
    assert "low_confidence" in resp.json()
    assert resp.json()["low_confidence"] is False

def test_predict_full_anomaly_sets_low_confidence_true(client):
    with patch("src.api.routes.check_anomaly", return_value=ANOMALY_TRUE):
        with patch("src.api.routes.store_anomaly") as mock_store:
            with patch("src.api.routes.get_weather", return_value=MOCK_WEATHER_FULL):
                resp = client.post("/api/v1/predict/full", json=FULL_PAYLOAD)
    assert resp.status_code == 200
    assert resp.json()["low_confidence"] is True
    mock_store.assert_called_once()

def test_predict_full_no_anomaly_does_not_call_store_anomaly(client):
    with patch("src.api.routes.check_anomaly", return_value=ANOMALY_FALSE):
        with patch("src.api.routes.store_anomaly") as mock_store:
            with patch("src.api.routes.get_weather", return_value=MOCK_WEATHER_FULL):
                client.post("/api/v1/predict/full", json=FULL_PAYLOAD)
    mock_store.assert_not_called()

def test_predict_full_store_anomaly_called_with_correct_tier(client):
    with patch("src.api.routes.check_anomaly", return_value=ANOMALY_TRUE):
        with patch("src.api.routes.store_anomaly") as mock_store:
            with patch("src.api.routes.get_weather", return_value=MOCK_WEATHER_FULL):
                client.post("/api/v1/predict/full", json=FULL_PAYLOAD)
    call_record = mock_store.call_args[0][0]
    assert call_record["tier"] == "full"
    assert call_record["low_confidence_prediction"] is True
    assert "z_scores" in call_record
    assert "flagged_features" in call_record
    assert "input_features" in call_record
```

All five tests must fail before implementing.

---

### Step 3 — modify routes.py

Add imports at the top of `src/api/routes.py`:

```python
from src.services.monitor import check_anomaly
from src.services.database import store_anomaly
```

**In the `/predict/full` route handler**, after assembling the 25-feature dict
and before calling the model:

```python
anomaly_result = check_anomaly(feature_dict)
if anomaly_result["is_anomaly"]:
    store_anomaly({
        "timestamp": datetime.utcnow().isoformat(),
        "tier": "full",
        "input_features": feature_dict,
        "z_scores": anomaly_result["z_scores"],
        "flagged_features": anomaly_result["flagged_features"],
        "low_confidence_prediction": True,
    })
```

Append to the response dict before returning:
```python
response["low_confidence"] = anomaly_result["is_anomaly"]
```

**In the `/predict/simple` route handler**, apply the same pattern using
`tier="simple"` in the `store_anomaly` call.

Confirm all five tests pass.

## Git

- **Branch:** `feat/015-low-confidence-flag-api`
- **Commit format:** `feat(api): call check_anomaly on every predict request, return low_confidence in response`
- **PR title:** `feat(api): add low_confidence field to predict responses — anomaly flag integration`
