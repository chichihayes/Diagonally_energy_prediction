---
id: "006"
slug: implement-predict-full-endpoint
feature: F1
epic: E2
title: Implement POST /api/v1/predict/full endpoint
status: open
---

# 006 — Implement POST /api/v1/predict/full endpoint

## Goal

`POST /api/v1/predict/full` accepts 19 sensor fields and a location, fetches
6 outside weather features automatically, assembles a 25-feature dict, runs
`model_full.joblib`, calculates the NGN cost, stores the result in Supabase,
and returns `predicted_wh`, `predicted_kwh`, and `estimated_cost_ngn` — all
within 2 seconds.

## User Story

As a developer integrating the Smart Home tier, I want a working API endpoint
at `POST /api/v1/predict/full` so that the scheduler and any other client can
submit sensor readings and receive a complete prediction response without
needing to know anything about the model or weather enrichment.

## Reference Docs

- `docs/api-contracts.md` — POST /api/v1/predict/full request/response shape and error codes
- `docs/schema.md` — model_full 25-feature column order, predictions table schema
- `docs/architecture.md` — Smart Home tier data flow, service boundary rules

## Acceptance Criteria

- [ ] `POST /api/v1/predict/full` with all 19 sensor fields + `location` returns HTTP 200
- [ ] Response body contains exactly: `predicted_wh` (float), `predicted_kwh` (float), `estimated_cost_ngn` (float)
- [ ] `predicted_kwh == predicted_wh / 1000` (within floating point tolerance)
- [ ] `estimated_cost_ngn == round(predicted_kwh * ELECTRICITY_TARIFF_NGN_PER_KWH, 2)`
- [ ] The 25-feature dict passed to `predict_full` has keys in the exact order: `lights, T1, RH_1, T2, RH_2, T3, RH_3, T4, RH_4, T5, RH_5, T6, RH_6, T7, RH_7, T8, RH_8, T9, RH_9, T_out, Press_mm_hg, RH_out, Windspeed, Visibility, Tdewpoint`
- [ ] `model_full` is loaded once at module import — not reloaded per request
- [ ] Prediction row is inserted into the Supabase `predictions` table with `tier="full"`
- [ ] Omitting any required sensor field returns HTTP 422
- [ ] If `get_weather` raises `HTTPException(500)`, the endpoint propagates the 500

## Files to Modify

- `src/model/predict.py` — add `_get_full_model()` singleton and `predict_full(features: dict) -> float`
- `src/services/features.py` — add `assemble_full_features(body: dict, weather: dict) -> dict`
- `src/api/routes.py` — add `FullPredictRequest` Pydantic model and `POST /api/v1/predict/full` handler

> `cost.py`, `database.py`, `weather.py`, and `main.py` already exist. Do not modify them unless a
> one-line import addition is needed in `routes.py`.

## Out of Scope

- APScheduler or automatic 15-minute submission (F2)
- Dashboard frontend (F3)
- History chart and table (F4)
- `model_simple` or `/api/v1/predict/simple`
- Monitoring / anomaly detection

## Implementation Plan

### Step 1 — predict.py: add predict_full singleton

**Test** (`tests/test_model.py`):
```python
def test_predict_full_returns_float(tmp_path, monkeypatch):
    import joblib
    import pandas as pd
    import pytest
    from sklearn.dummy import DummyRegressor

    features = {
        "lights": 0, "T1": 19.89, "RH_1": 47.6, "T2": 19.2, "RH_2": 44.79,
        "T3": 19.79, "RH_3": 44.73, "T4": 17.17, "RH_4": 41.67, "T5": 17.2,
        "RH_5": 55.2, "T6": 7.03, "RH_6": 84.26, "T7": 17.2, "RH_7": 41.63,
        "T8": 18.2, "RH_8": 48.9, "T9": 17.03, "RH_9": 45.53,
        "T_out": 6.6, "Press_mm_hg": 733.5, "RH_out": 92.0,
        "Windspeed": 7.0, "Visibility": 63.0, "Tdewpoint": 5.3,
    }
    dummy = DummyRegressor(strategy="constant", constant=84.3)
    dummy.fit(pd.DataFrame([features]), [84.3])
    model_path = tmp_path / "model_full.joblib"
    joblib.dump(dummy, str(model_path))
    monkeypatch.setenv("MODEL_PATH_FULL", str(model_path))

    from src.model import predict as predict_module
    import importlib
    importlib.reload(predict_module)

    result = predict_module.predict_full(features)
    assert isinstance(result, float)
    assert result == pytest.approx(84.3)
```

**File:** `src/model/predict.py` — add below existing `_model_simple` block:

```python
_model_full = None

def _get_full_model():
    global _model_full
    if _model_full is None:
        path = os.environ.get("MODEL_PATH_FULL", "src/model/trained/model_full.joblib")
        _model_full = joblib.load(path)
    return _model_full

def predict_full(features: dict) -> float:
    model = _get_full_model()
    df = pd.DataFrame([features])
    return float(model.predict(df)[0])
```

---

### Step 2 — features.py: assemble 25-feature dict from request body + weather

**Test** (`tests/test_features.py`):
```python
def test_assemble_full_features_returns_25_keys_in_order():
    from src.services.features import assemble_full_features
    body = {
        "lights": 0, "T1": 19.89, "RH_1": 47.6, "T2": 19.2, "RH_2": 44.79,
        "T3": 19.79, "RH_3": 44.73, "T4": 17.17, "RH_4": 41.67, "T5": 17.2,
        "RH_5": 55.2, "T6": 7.03, "RH_6": 84.26, "T7": 17.2, "RH_7": 41.63,
        "T8": 18.2, "RH_8": 48.9, "T9": 17.03, "RH_9": 45.53,
    }
    weather = {
        "T_out": 6.6, "Press_mm_hg": 733.5, "RH_out": 92.0,
        "Windspeed": 7.0, "Visibility": 63.0, "Tdewpoint": 5.3,
    }
    result = assemble_full_features(body, weather)
    expected_keys = [
        "lights", "T1", "RH_1", "T2", "RH_2", "T3", "RH_3", "T4", "RH_4",
        "T5", "RH_5", "T6", "RH_6", "T7", "RH_7", "T8", "RH_8", "T9", "RH_9",
        "T_out", "Press_mm_hg", "RH_out", "Windspeed", "Visibility", "Tdewpoint",
    ]
    assert list(result.keys()) == expected_keys
    assert len(result) == 25

def test_assemble_full_features_merges_weather_values():
    from src.services.features import assemble_full_features
    body = {
        "lights": 100, "T1": 20.0, "RH_1": 50.0, "T2": 20.0, "RH_2": 50.0,
        "T3": 20.0, "RH_3": 50.0, "T4": 20.0, "RH_4": 50.0, "T5": 20.0,
        "RH_5": 50.0, "T6": 20.0, "RH_6": 50.0, "T7": 20.0, "RH_7": 50.0,
        "T8": 20.0, "RH_8": 50.0, "T9": 20.0, "RH_9": 50.0,
    }
    weather = {
        "T_out": 28.0, "Press_mm_hg": 760.0, "RH_out": 80.0,
        "Windspeed": 5.0, "Visibility": 10.0, "Tdewpoint": 22.0,
    }
    result = assemble_full_features(body, weather)
    assert result["T_out"] == 28.0
    assert result["Press_mm_hg"] == 760.0
    assert result["lights"] == 100
```

**File:** `src/services/features.py` — add:

```python
def assemble_full_features(body: dict, weather: dict) -> dict:
    return {
        "lights": body["lights"],
        "T1": body["T1"], "RH_1": body["RH_1"],
        "T2": body["T2"], "RH_2": body["RH_2"],
        "T3": body["T3"], "RH_3": body["RH_3"],
        "T4": body["T4"], "RH_4": body["RH_4"],
        "T5": body["T5"], "RH_5": body["RH_5"],
        "T6": body["T6"], "RH_6": body["RH_6"],
        "T7": body["T7"], "RH_7": body["RH_7"],
        "T8": body["T8"], "RH_8": body["RH_8"],
        "T9": body["T9"], "RH_9": body["RH_9"],
        "T_out": weather["T_out"],
        "Press_mm_hg": weather["Press_mm_hg"],
        "RH_out": weather["RH_out"],
        "Windspeed": weather["Windspeed"],
        "Visibility": weather["Visibility"],
        "Tdewpoint": weather["Tdewpoint"],
    }
```

---

### Step 3 — routes.py + main.py: wire up the endpoint

No new test in this step — the endpoint integration tests are in issue 007.

**File:** `src/api/routes.py` — add below existing `SimplePredictRequest`:

```python
from src.model.predict import predict_full
from src.services.features import assemble_full_features

class FullPredictRequest(BaseModel):
    lights: int
    T1: float;  RH_1: float
    T2: float;  RH_2: float
    T3: float;  RH_3: float
    T4: float;  RH_4: float
    T5: float;  RH_5: float
    T6: float;  RH_6: float
    T7: float;  RH_7: float
    T8: float;  RH_8: float
    T9: float;  RH_9: float
    location: str

@router.post("/api/v1/predict/full")
def predict_full_endpoint(body: FullPredictRequest):
    weather = get_weather(body.location)
    features = assemble_full_features(body.dict(exclude={"location"}), weather)
    predicted_wh = predict_full(features)
    predicted_kwh, estimated_cost_ngn = wh_to_cost(predicted_wh)
    insert_prediction({
        "tier": "full",
        "predicted_wh": predicted_wh,
        "predicted_kwh": predicted_kwh,
        "estimated_cost_ngn": estimated_cost_ngn,
        "location": body.location,
        "inputs": features,
    })
    return {
        "predicted_wh": predicted_wh,
        "predicted_kwh": predicted_kwh,
        "estimated_cost_ngn": estimated_cost_ngn,
    }
```

No changes to `src/api/main.py` — the router is already registered.

## Git

- **Branch:** `feat/006-predict-full-endpoint`
- **Commit format:** `feat(api): implement POST /api/v1/predict/full with weather fetch, inference, cost, and Supabase insert`
- **PR title:** `feat(api): implement POST /api/v1/predict/full`
