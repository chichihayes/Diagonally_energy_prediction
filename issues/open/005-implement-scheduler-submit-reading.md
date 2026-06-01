---
id: "005"
slug: implement-scheduler-submit-reading
feature: F2
epic: E2
title: Implement assemble_full_features, predict_full, and submit_smart_home_reading
status: open
---

# 005 — Implement `submit_smart_home_reading()` in `scheduler.py`

## Goal

A single callable function `submit_smart_home_reading()` reads the latest sensor
readings from environment variables, fetches outside weather data, assembles the
full 25-feature vector, runs the full regression model, calculates the NGN cost,
and stores the result in Supabase — silently catching and logging any failure so
the scheduler tick never crashes.

## User Story

As a Smart Home homeowner, I want sensor readings submitted and stored automatically
every 15 minutes so predictions accumulate on my dashboard without any manual input
from me.

## Reference Docs

- `docs/architecture.md` — Smart Home tier data flow; service boundary rules
- `docs/api-contracts.md` — POST /api/v1/predict/full feature list and response shape
- `CLAUDE.md` — scheduler conventions: log and return on failure, never raise
- `CLAUDE.md` — ML conventions: full model 25-feature list and column order

## Acceptance Criteria

- [ ] `assemble_full_features(lights, sensors, weather) -> dict` returns a dict with
      exactly the 25 keys in CLAUDE.md feature order: `lights`, `T1`, `RH_1` … `T9`,
      `RH_9`, `T_out`, `Press_mm_hg`, `RH_out`, `Windspeed`, `Visibility`, `Tdewpoint`
- [ ] `predict_full(features: dict) -> float` loads `model_full.joblib` once as a
      module-level singleton and returns a float; it never reloads the model per call
- [ ] `submit_smart_home_reading()` reads sensor values from env vars `SENSOR_LIGHTS`,
      `SENSOR_T1`–`SENSOR_T9`, `SENSOR_RH_1`–`SENSOR_RH_9`, `SENSOR_LOCATION`
      (defaults: lights=0, temps=20.0, humidities=50.0, location="Lagos")
- [ ] If `get_weather` raises any exception, the function logs it and returns `None` —
      it does not re-raise
- [ ] If `predict_full` raises any exception, the function logs it and returns `None` —
      it does not re-raise
- [ ] If `insert_prediction` raises any exception, the function logs it and returns
      `None` — it does not re-raise
- [ ] The prediction row inserted into Supabase contains `tier="full"`

## Files to Modify

- `src/services/features.py` — add `assemble_full_features(lights, sensors, weather)`
- `src/model/predict.py` — add `predict_full(features: dict) -> float` singleton
- `src/services/scheduler.py` — create with `_read_sensors()` and `submit_smart_home_reading()`
- `tests/test_features.py` — add full-feature assembly tests
- `tests/test_model.py` — add `predict_full` singleton test

## Out of Scope

- APScheduler wiring into `main.py` (issue 006)
- Scheduler integration tests for exception paths and startup (issue 007)
- Real Zigbee hardware integration
- Drift detection or anomaly flagging (E5 epic)

## Implementation Plan

### Step 1 — `assemble_full_features` in `features.py`

**Tests** (`tests/test_features.py` — must fail before implementation):
```python
def test_assemble_full_features_returns_25_keys_in_order():
    from src.services.features import assemble_full_features
    sensors = {
        "T1": 19.89, "RH_1": 47.6,
        "T2": 19.2,  "RH_2": 44.79,
        "T3": 19.79, "RH_3": 44.73,
        "T4": 17.17, "RH_4": 41.67,
        "T5": 17.2,  "RH_5": 55.2,
        "T6": 7.03,  "RH_6": 84.26,
        "T7": 17.2,  "RH_7": 41.63,
        "T8": 18.2,  "RH_8": 48.9,
        "T9": 17.03, "RH_9": 45.53,
    }
    weather = {
        "T_out": 28.4, "Press_mm_hg": 1012.0,
        "RH_out": 82.0, "Windspeed": 3.1,
        "Visibility": 10.0, "Tdewpoint": 25.1,
    }
    result = assemble_full_features(lights=0, sensors=sensors, weather=weather)
    expected_keys = [
        "lights",
        "T1", "RH_1", "T2", "RH_2", "T3", "RH_3", "T4", "RH_4",
        "T5", "RH_5", "T6", "RH_6", "T7", "RH_7", "T8", "RH_8", "T9", "RH_9",
        "T_out", "Press_mm_hg", "RH_out", "Windspeed", "Visibility", "Tdewpoint",
    ]
    assert list(result.keys()) == expected_keys
    assert len(result) == 25
    assert result["lights"] == 0
    assert result["T1"] == 19.89
    assert result["T_out"] == 28.4
    assert result["Press_mm_hg"] == 1012.0

def test_assemble_full_features_preserves_all_sensor_values():
    from src.services.features import assemble_full_features
    sensors = {f"T{i}": float(i) for i in range(1, 10)}
    sensors.update({f"RH_{i}": float(i * 10) for i in range(1, 10)})
    weather = {
        "T_out": 30.0, "Press_mm_hg": 1010.0,
        "RH_out": 75.0, "Windspeed": 4.0,
        "Visibility": 12.0, "Tdewpoint": 22.0,
    }
    result = assemble_full_features(lights=50, sensors=sensors, weather=weather)
    assert result["T3"] == 3.0
    assert result["RH_7"] == 70.0
    assert result["Windspeed"] == 4.0
    assert result["lights"] == 50
```

**File:** `src/services/features.py` — add:
```python
def assemble_full_features(lights: int, sensors: dict, weather: dict) -> dict:
    return {
        "lights": lights,
        "T1": sensors["T1"],   "RH_1": sensors["RH_1"],
        "T2": sensors["T2"],   "RH_2": sensors["RH_2"],
        "T3": sensors["T3"],   "RH_3": sensors["RH_3"],
        "T4": sensors["T4"],   "RH_4": sensors["RH_4"],
        "T5": sensors["T5"],   "RH_5": sensors["RH_5"],
        "T6": sensors["T6"],   "RH_6": sensors["RH_6"],
        "T7": sensors["T7"],   "RH_7": sensors["RH_7"],
        "T8": sensors["T8"],   "RH_8": sensors["RH_8"],
        "T9": sensors["T9"],   "RH_9": sensors["RH_9"],
        "T_out": weather["T_out"],
        "Press_mm_hg": weather["Press_mm_hg"],
        "RH_out": weather["RH_out"],
        "Windspeed": weather["Windspeed"],
        "Visibility": weather["Visibility"],
        "Tdewpoint": weather["Tdewpoint"],
    }
```

---

### Step 2 — `predict_full` singleton in `predict.py`

**Test** (`tests/test_model.py` — must fail before implementation):
```python
def test_predict_full_returns_float(tmp_path, monkeypatch):
    import joblib, pytest
    from sklearn.dummy import DummyRegressor
    import pandas as pd
    cols = [
        "lights", "T1", "RH_1", "T2", "RH_2", "T3", "RH_3", "T4", "RH_4",
        "T5", "RH_5", "T6", "RH_6", "T7", "RH_7", "T8", "RH_8", "T9", "RH_9",
        "T_out", "Press_mm_hg", "RH_out", "Windspeed", "Visibility", "Tdewpoint",
    ]
    dummy = DummyRegressor(strategy="constant", constant=150.0)
    X = pd.DataFrame([{c: 1.0 for c in cols}])
    dummy.fit(X, [150.0])
    model_path = tmp_path / "model_full.joblib"
    joblib.dump(dummy, str(model_path))
    monkeypatch.setenv("MODEL_PATH_FULL", str(model_path))

    from src.model import predict as predict_module
    import importlib; importlib.reload(predict_module)

    result = predict_module.predict_full({c: 1.0 for c in cols})
    assert isinstance(result, float)
    assert result == pytest.approx(150.0)
```

**File:** `src/model/predict.py` — add after existing `_model_simple` block:
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

### Step 3 — implement `scheduler.py`

No unit tests here — exception path and startup tests are in issue 007. Confirm the
module imports without error after step 1 and step 2 are done.

**File:** `src/services/scheduler.py` — create:
```python
import logging
import os

from src.services.weather import get_weather
from src.services.features import assemble_full_features
from src.model.predict import predict_full
from src.services.cost import wh_to_cost
from src.services.database import insert_prediction

logger = logging.getLogger(__name__)


def _read_sensors() -> tuple[int, dict]:
    lights = int(os.environ.get("SENSOR_LIGHTS", "0"))
    sensors = {}
    for i in range(1, 10):
        sensors[f"T{i}"] = float(os.environ.get(f"SENSOR_T{i}", "20.0"))
        sensors[f"RH_{i}"] = float(os.environ.get(f"SENSOR_RH_{i}", "50.0"))
    return lights, sensors


def submit_smart_home_reading() -> None:
    location = os.environ.get("SENSOR_LOCATION", "Lagos")
    lights, sensors = _read_sensors()

    try:
        weather = get_weather(location)
    except Exception:
        logger.exception("Scheduler: weather fetch failed — skipping tick")
        return

    features = assemble_full_features(lights, sensors, weather)

    try:
        predicted_wh = predict_full(features)
    except Exception:
        logger.exception("Scheduler: model inference failed — skipping tick")
        return

    predicted_kwh, estimated_cost_ngn = wh_to_cost(predicted_wh)

    try:
        insert_prediction({
            "tier": "full",
            "predicted_wh": predicted_wh,
            "predicted_kwh": predicted_kwh,
            "estimated_cost_ngn": estimated_cost_ngn,
            "location": location,
            "inputs": features,
        })
    except Exception:
        logger.exception("Scheduler: Supabase insert failed — skipping tick")
        return
```

## Git

- **Branch:** `feat/005-implement-scheduler-submit-reading`
- **Commit format:** `feat(scheduler): implement assemble_full_features, predict_full, and submit_smart_home_reading with silent error handling`
- **PR title:** `feat(scheduler): implement submit_smart_home_reading()`
