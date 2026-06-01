---
id: "003"
slug: implement-predict-simple-endpoint
feature: F1
epic: E1
title: Implement POST /api/v1/predict/simple endpoint
status: open
---

# 003 — Implement POST /api/v1/predict/simple endpoint

## Goal

The endpoint `POST /api/v1/predict/simple` accepts `lights`, `T1`, and `location`,
assembles the 7-feature vector, runs inference, calculates the NGN cost, stores the
prediction in Supabase, and returns the full JSON response — all within 2 seconds.

## User Story

As a homeowner using the Basic tier, I want to POST my lights reading, one room
temperature, and city name and receive a prediction of my appliance energy consumption
and its estimated cost in Naira so I can understand my energy usage without owning
any sensors.

## Reference Docs

- `docs/api-contracts.md` — POST /api/v1/predict/simple request/response shape
- `docs/schema.md` — model_simple 7-feature list and predictions table schema
- `docs/architecture.md` — Basic tier data flow, service boundary rules

## Acceptance Criteria

- [ ] `POST /api/v1/predict/simple` with `{"lights": 0, "T1": 19.89, "location": "Lagos"}` returns HTTP 200
- [ ] Response body contains exactly: `predicted_wh` (float), `predicted_kwh` (float), `estimated_cost_ngn` (float), `weather_factors` (object)
- [ ] `predicted_kwh == predicted_wh / 1000` (within floating point tolerance)
- [ ] `estimated_cost_ngn == round(predicted_kwh * ELECTRICITY_TARIFF_NGN_PER_KWH, 2)`
- [ ] `weather_factors` contains exactly: `T_out`, `RH_out`, `Windspeed`, `Visibility`, `Tdewpoint`
- [ ] Omitting any required field returns HTTP 422
- [ ] If `get_weather` raises HTTPException 500, the endpoint propagates the 500 to the caller
- [ ] The prediction row is inserted into the Supabase `predictions` table with `tier="simple"`
- [ ] Model is loaded once at module import — not reloaded per request
- [ ] Response time is under 2 seconds on a warm cache (weather cached, model loaded)

## Files to Modify

- `src/model/predict.py` — create `load_simple_model()` singleton and `predict_simple(features: dict) -> float`
- `src/services/features.py` — add `assemble_simple_features(lights, T1, weather: dict) -> dict`
- `src/services/cost.py` — create `wh_to_cost(predicted_wh: float) -> tuple[float, float]` returning `(predicted_kwh, estimated_cost_ngn)`
- `src/services/database.py` — create `insert_prediction(row: dict) -> None`
- `src/api/routes.py` — add `POST /api/v1/predict/simple` route handler
- `src/api/main.py` — register router with FastAPI app

## Out of Scope

- `POST /api/v1/predict/full` (full tier)
- Prediction history endpoint
- Frontend display
- Scheduler integration
- model_forecast

## Implementation Plan

### Step 1 — cost.py: Wh → NGN conversion

**Test** (`tests/test_cost.py`):
```python
import os, pytest

def test_wh_to_cost_converts_correctly(monkeypatch):
    monkeypatch.setenv("ELECTRICITY_TARIFF_NGN_PER_KWH", "68.00")
    from src.services.cost import wh_to_cost
    kwh, cost = wh_to_cost(1000.0)
    assert kwh == pytest.approx(1.0)
    assert cost == pytest.approx(68.00)

def test_wh_to_cost_rounds_to_2dp(monkeypatch):
    monkeypatch.setenv("ELECTRICITY_TARIFF_NGN_PER_KWH", "68.00")
    from src.services.cost import wh_to_cost
    _, cost = wh_to_cost(60.5)
    assert cost == round(0.0605 * 68.00, 2)

def test_wh_to_cost_reads_tariff_from_env(monkeypatch):
    monkeypatch.setenv("ELECTRICITY_TARIFF_NGN_PER_KWH", "100.00")
    from src.services import cost as cost_module
    import importlib; importlib.reload(cost_module)
    _, ngn = cost_module.wh_to_cost(1000.0)
    assert ngn == pytest.approx(100.00)
```

**File:** `src/services/cost.py`

```python
import os

def wh_to_cost(predicted_wh: float) -> tuple[float, float]:
    tariff = float(os.environ["ELECTRICITY_TARIFF_NGN_PER_KWH"])
    kwh = predicted_wh / 1000.0
    cost = round(kwh * tariff, 2)
    return kwh, cost
```

---

### Step 2 — features.py: assemble simple feature dict

**Test** (`tests/test_features.py`):
```python
def test_assemble_simple_features_returns_correct_keys():
    from src.services.features import assemble_simple_features
    weather = {"T_out": 28.4, "RH_out": 82.0, "Windspeed": 3.1, "Visibility": 10.0, "Tdewpoint": 25.1}
    result = assemble_simple_features(lights=0, T1=19.89, weather=weather)
    assert list(result.keys()) == ["lights", "T1", "T_out", "RH_out", "Windspeed", "Visibility", "Tdewpoint"]
    assert result["lights"] == 0
    assert result["T1"] == 19.89
    assert result["T_out"] == 28.4

def test_assemble_simple_features_preserves_weather_values():
    from src.services.features import assemble_simple_features
    weather = {"T_out": 30.0, "RH_out": 70.0, "Windspeed": 5.0, "Visibility": 8.0, "Tdewpoint": 22.0}
    result = assemble_simple_features(lights=100, T1=22.5, weather=weather)
    assert result["Windspeed"] == 5.0
    assert result["Visibility"] == 8.0
```

**File:** `src/services/features.py` — add:

```python
def assemble_simple_features(lights: int, T1: float, weather: dict) -> dict:
    return {
        "lights": lights,
        "T1": T1,
        "T_out": weather["T_out"],
        "RH_out": weather["RH_out"],
        "Windspeed": weather["Windspeed"],
        "Visibility": weather["Visibility"],
        "Tdewpoint": weather["Tdewpoint"],
    }
```

---

### Step 3 — predict.py: load model_simple singleton + inference

**Test** (`tests/test_model.py`):
```python
def test_predict_simple_returns_float(tmp_path, monkeypatch):
    import joblib, numpy as np
    from sklearn.dummy import DummyRegressor
    import pandas as pd
    dummy = DummyRegressor(strategy="constant", constant=60.5)
    X = pd.DataFrame([{"lights": 0, "T1": 20.0, "T_out": 28.0,
                        "RH_out": 80.0, "Windspeed": 3.0,
                        "Visibility": 10.0, "Tdewpoint": 25.0}])
    dummy.fit(X, [60.5])
    model_path = tmp_path / "model_simple.joblib"
    joblib.dump(dummy, str(model_path))
    monkeypatch.setenv("MODEL_PATH_SIMPLE", str(model_path))

    from src.model import predict as predict_module
    import importlib; importlib.reload(predict_module)

    features = {"lights": 0, "T1": 20.0, "T_out": 28.0,
                 "RH_out": 80.0, "Windspeed": 3.0,
                 "Visibility": 10.0, "Tdewpoint": 25.0}
    result = predict_module.predict_simple(features)
    assert isinstance(result, float)
    assert result == pytest.approx(60.5)
```

**File:** `src/model/predict.py`

```python
import os
import joblib
import pandas as pd

_model_simple = None

def _get_simple_model():
    global _model_simple
    if _model_simple is None:
        path = os.environ.get("MODEL_PATH_SIMPLE", "src/model/trained/model_simple.joblib")
        _model_simple = joblib.load(path)
    return _model_simple

def predict_simple(features: dict) -> float:
    model = _get_simple_model()
    df = pd.DataFrame([features])
    return float(model.predict(df)[0])
```

---

### Step 4 — database.py: insert prediction row

**Test** (`tests/test_database.py`):
```python
from unittest.mock import patch, MagicMock

def test_insert_prediction_calls_supabase_insert():
    from src.services.database import insert_prediction
    mock_client = MagicMock()
    mock_client.table.return_value.insert.return_value.execute.return_value = MagicMock()
    with patch("src.services.database._get_client", return_value=mock_client):
        insert_prediction({
            "tier": "simple",
            "predicted_wh": 60.5,
            "predicted_kwh": 0.0605,
            "estimated_cost_ngn": 4.11,
            "location": "Lagos",
            "inputs": {"lights": 0, "T1": 19.89},
        })
    mock_client.table.assert_called_once_with("predictions")
    mock_client.table.return_value.insert.assert_called_once()
```

**File:** `src/services/database.py`

```python
import os
from supabase import create_client, Client

_client: Client | None = None

def _get_client() -> Client:
    global _client
    if _client is None:
        _client = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_ANON_KEY"])
    return _client

def insert_prediction(row: dict) -> None:
    _get_client().table("predictions").insert(row).execute()
```

---

### Step 5 — routes.py + main.py: wire up the endpoint

**File:** `src/api/routes.py`

```python
from fastapi import APIRouter
from pydantic import BaseModel
from src.services.weather import get_weather
from src.services.features import assemble_simple_features
from src.model.predict import predict_simple
from src.services.cost import wh_to_cost
from src.services.database import insert_prediction

router = APIRouter()

class SimplePredictRequest(BaseModel):
    lights: int
    T1: float
    location: str

@router.post("/api/v1/predict/simple")
def predict_simple_endpoint(body: SimplePredictRequest):
    weather = get_weather(body.location)
    features = assemble_simple_features(body.lights, body.T1, weather)
    predicted_wh = predict_simple(features)
    predicted_kwh, estimated_cost_ngn = wh_to_cost(predicted_wh)
    insert_prediction({
        "tier": "simple",
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
        "weather_factors": weather,
    }
```

**File:** `src/api/main.py`

```python
from fastapi import FastAPI
from src.api.routes import router

app = FastAPI()
app.include_router(router)
```

## Git

- **Branch:** `feat/003-predict-simple-endpoint`
- **Commit format:** `feat(api): implement POST /api/v1/predict/simple with weather fetch, inference, cost, and Supabase insert`
- **PR title:** `feat(api): implement POST /api/v1/predict/simple`
