---
id: "009"
slug: implement-forecast-py
feature: F1
epic: E3
title: Implement forecast.py — model singleton and forecast_24h function
status: open
---

# 009 — Implement forecast.py — model singleton and forecast_24h function

## Goal

`src/model/forecast.py` loads `model_forecast.joblib` once at startup as a
module-level singleton and exposes a `forecast_24h(location: str) -> list[dict]`
function that returns 24 hourly dicts with yhat, yhat_lower, yhat_upper,
predicted_kwh, and estimated_cost_ngn — ready for the route handler to consume.

## User Story

As the route handler for `GET /api/v1/forecast/24h`, I want a single
`forecast_24h(location)` call in `forecast.py` that fetches weather, runs the
model, and applies cost conversion, so the route only has to post-process
`peak_hour` and `lowest_hour` without knowing anything about the model internals.

## Reference Docs

- `docs/schema.md` — forecast output schema: ds, yhat, yhat_lower, yhat_upper, predicted_kwh, estimated_cost_ngn
- `docs/architecture.md` — service boundaries: forecast.py loads model singleton, calls weather.py, returns list of dicts; cost.py converts Wh→NGN
- `CLAUDE.md` — ML conventions: model loaded once at startup as singleton, never reloaded per request; cost always read from env var

## Acceptance Criteria

- [ ] `_model` (or `_artifact`) is assigned once at module import — multiple imports reuse the same object
- [ ] `forecast_24h("Lagos")` returns a list of exactly 24 dicts
- [ ] Each dict contains exactly these keys: `ds`, `yhat`, `yhat_lower`, `yhat_upper`, `predicted_kwh`, `estimated_cost_ngn`
- [ ] `predicted_kwh == round(yhat / 1000, 3)` for every entry
- [ ] `estimated_cost_ngn == round(predicted_kwh * float(os.environ["ELECTRICITY_TARIFF_NGN_PER_KWH"]), 2)` for every entry
- [ ] All 24 `ds` values are consecutive ISO-format hourly timestamps starting at the next whole hour from `datetime.now()`
- [ ] `yhat_lower <= yhat <= yhat_upper` for every entry
- [ ] An exception raised by the underlying model propagates out of `forecast_24h` — not caught silently

## Files to Modify

- `src/model/forecast.py` — create

> Do not touch `routes.py` (issue 010), `test_api.py` (issue 011), or `cost.py`.
> Call `cost.py`'s `wh_to_ngn` helper if it exists; otherwise apply the formula directly.

## Out of Scope

- The route handler that calls `forecast_24h` (issue 010)
- API-level tests (issue 011)
- 7-day forecast function (F2)
- Saving predictions to Supabase (not required for the forecast flow per architecture.md)

## Implementation Plan

### Step 1 — forecast.py: singleton loader

The artifact saved by issue 008 is `{"model": <model_obj>, "model_type": <str>}`.
Load it at module level so every call to `forecast_24h` reuses the same object.

**Test** (`tests/test_forecast.py`):
```python
def test_forecast_model_singleton_is_same_object(monkeypatch, tmp_path):
    import joblib, importlib
    # Write a minimal stub artifact
    stub = {"model": object(), "model_type": "Prophet"}
    p = tmp_path / "model_forecast.joblib"
    joblib.dump(stub, str(p))
    monkeypatch.setenv("MODEL_PATH_FORECAST", str(p))
    import src.model.forecast as f_mod
    importlib.reload(f_mod)
    assert f_mod._artifact is f_mod._artifact  # same object, not reloaded
```

**File:** `src/model/forecast.py` — start with:

```python
import os
import joblib

_artifact = joblib.load(os.environ.get("MODEL_PATH_FORECAST", "src/model/trained/model_forecast.joblib"))
```

---

### Step 2 — forecast_24h: generate 24 dicts with all required fields

Dispatch inference by `_artifact["model_type"]`:
- `"Prophet"` — call `model.predict(future_df)` where `future_df` has `ds` column for next 24 hours
- `"XGBoost_lags"` / `"LightGBM_lags"` — call `model.predict(X_future)` for each hour; use ±15% of yhat as yhat_lower/yhat_upper
- `"LSTM"` / `"TFT"` — call neuralforecast's `predict()` method

After inference, apply cost conversion per CLAUDE.md:
```
predicted_kwh = round(yhat / 1000, 3)
estimated_cost_ngn = round(predicted_kwh * float(os.environ["ELECTRICITY_TARIFF_NGN_PER_KWH"]), 2)
```

**Test** (`tests/test_forecast.py`):
```python
import os
import pandas as pd
from unittest.mock import MagicMock, patch

def _make_mock_artifact(yhat=200.0):
    mock_model = MagicMock()
    mock_model.predict.return_value = pd.DataFrame({
        "ds": pd.date_range("2026-06-01", periods=24, freq="h"),
        "yhat": [yhat] * 24,
        "yhat_lower": [yhat * 0.85] * 24,
        "yhat_upper": [yhat * 1.15] * 24,
    })
    return {"model": mock_model, "model_type": "Prophet"}

def test_forecast_24h_returns_24_elements(monkeypatch):
    import src.model.forecast as f_mod
    monkeypatch.setattr(f_mod, "_artifact", _make_mock_artifact())
    monkeypatch.setattr("src.services.weather.fetch_weather", lambda loc: {})
    os.environ["ELECTRICITY_TARIFF_NGN_PER_KWH"] = "68.00"
    result = f_mod.forecast_24h("Lagos")
    assert len(result) == 24

def test_forecast_24h_each_dict_has_required_keys(monkeypatch):
    import src.model.forecast as f_mod
    monkeypatch.setattr(f_mod, "_artifact", _make_mock_artifact())
    monkeypatch.setattr("src.services.weather.fetch_weather", lambda loc: {})
    os.environ["ELECTRICITY_TARIFF_NGN_PER_KWH"] = "68.00"
    result = f_mod.forecast_24h("Lagos")
    required = {"ds", "yhat", "yhat_lower", "yhat_upper", "predicted_kwh", "estimated_cost_ngn"}
    for item in result:
        assert set(item.keys()) == required

def test_forecast_24h_cost_calculation(monkeypatch):
    import src.model.forecast as f_mod
    monkeypatch.setattr(f_mod, "_artifact", _make_mock_artifact(yhat=1000.0))
    monkeypatch.setattr("src.services.weather.fetch_weather", lambda loc: {})
    os.environ["ELECTRICITY_TARIFF_NGN_PER_KWH"] = "68.00"
    result = f_mod.forecast_24h("Lagos")
    assert result[0]["predicted_kwh"] == 1.0
    assert result[0]["estimated_cost_ngn"] == 68.0

def test_forecast_24h_lower_lte_yhat_lte_upper(monkeypatch):
    import src.model.forecast as f_mod
    monkeypatch.setattr(f_mod, "_artifact", _make_mock_artifact(yhat=300.0))
    monkeypatch.setattr("src.services.weather.fetch_weather", lambda loc: {})
    os.environ["ELECTRICITY_TARIFF_NGN_PER_KWH"] = "68.00"
    result = f_mod.forecast_24h("Lagos")
    for item in result:
        assert item["yhat_lower"] <= item["yhat"] <= item["yhat_upper"]

def test_forecast_24h_propagates_model_exception(monkeypatch):
    import pytest, src.model.forecast as f_mod
    mock_model = MagicMock()
    mock_model.predict.side_effect = RuntimeError("model crashed")
    monkeypatch.setattr(f_mod, "_artifact", {"model": mock_model, "model_type": "Prophet"})
    monkeypatch.setattr("src.services.weather.fetch_weather", lambda loc: {})
    os.environ["ELECTRICITY_TARIFF_NGN_PER_KWH"] = "68.00"
    with pytest.raises(RuntimeError, match="model crashed"):
        f_mod.forecast_24h("Lagos")
```

## Git

- **Branch:** `feat/009-implement-forecast-py`
- **Commit format:** `feat(forecast): implement forecast.py singleton and forecast_24h function`
- **PR title:** `feat(forecast): implement forecast.py with 24h inference function`
