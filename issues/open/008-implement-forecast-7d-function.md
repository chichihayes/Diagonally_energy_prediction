---
id: "008"
slug: implement-forecast-7d-function
feature: F2
epic: E3
title: Implement forecast_7d in src/model/forecast.py
status: open
---

# 008 — Implement `forecast_7d` in `src/model/forecast.py`

## Goal

`forecast_7d()` generates 7 daily predictions from the loaded forecast model
singleton, converts each to watt-hours with confidence bounds and an NGN cost,
and identifies which day-of-week has the peak and lowest consumption — so the
API route has a single function to call with no raw model output leaking out.

## User Story

As a homeowner planning ahead, I want the system to produce a 7-day daily
forecast so I can see which days are likely to be energy-hungry before they
arrive.

## Reference Docs

- `docs/schema.md` — Forecast Output Schema (yhat, yhat_lower, yhat_upper,
  predicted_kwh, estimated_cost_ngn)
- `docs/api-contracts.md` — GET /api/v1/forecast/7d response shape (date,
  predicted_wh, predicted_kwh, lower_wh, upper_wh, estimated_cost_ngn,
  peak_day, lowest_day)
- `docs/decisions.md` — why forecast models return confidence intervals

## Acceptance Criteria

- [ ] `forecast_7d()` returns a dict with keys `forecast`, `peak_day`, `lowest_day`
- [ ] `forecast["forecast"]` is a list of exactly 7 dicts
- [ ] Each dict has keys: `date` (YYYY-MM-DD string), `predicted_wh`, `predicted_kwh`, `lower_wh`, `upper_wh`, `estimated_cost_ngn`
- [ ] `predicted_kwh == round(predicted_wh / 1000, 6)` for every row
- [ ] `estimated_cost_ngn` is read from `ELECTRICITY_TARIFF_NGN_PER_KWH` env var — never hardcoded
- [ ] `peak_day` is the full day name (e.g. `"Tuesday"`) of the row with the highest `predicted_wh`
- [ ] `lowest_day` is the full day name of the row with the lowest `predicted_wh`
- [ ] The model is **not** reloaded on each call — the module-level singleton is used
- [ ] Raw model output (Prophet DataFrame / LSTM array) is never returned to the caller

## Files to Modify

- `src/model/forecast.py` — add `forecast_7d()` alongside the existing model singleton loader

## Out of Scope

- GET /api/v1/forecast/7d route (issue 010)
- Bill projection calculation (issue 009)
- 24-hour forecast (already handled by `forecast_24h`)
- Model retraining

## Implementation Plan

### Step 1 — failing test: `forecast_7d` returns a 7-element list

**Test** (`tests/test_forecast.py`):
```python
import pytest
from unittest.mock import patch
import pandas as pd
from datetime import date, timedelta

def _make_mock_prophet_output() -> pd.DataFrame:
    today = date.today()
    rows = []
    for i in range(7):
        rows.append({
            "ds": pd.Timestamp(today + timedelta(days=i)),
            "yhat": 6000.0 + i * 100,
            "yhat_lower": 4000.0 + i * 100,
            "yhat_upper": 8000.0 + i * 100,
        })
    return pd.DataFrame(rows)

def test_forecast_7d_returns_7_element_list():
    from src.model.forecast import forecast_7d
    mock_df = _make_mock_prophet_output()
    with patch("src.model.forecast._model") as mock_model, \
         patch.dict("os.environ", {"ELECTRICITY_TARIFF_NGN_PER_KWH": "68.00"}):
        mock_model.predict.return_value = mock_df
        result = forecast_7d()
    assert len(result["forecast"]) == 7
```

Confirm it fails (`AttributeError` or `ImportError` — `forecast_7d` does not exist yet).

---

### Step 2 — failing test: each row has required keys

**Test** (`tests/test_forecast.py`):
```python
def test_forecast_7d_each_row_has_required_keys():
    from src.model.forecast import forecast_7d
    mock_df = _make_mock_prophet_output()
    with patch("src.model.forecast._model") as mock_model, \
         patch.dict("os.environ", {"ELECTRICITY_TARIFF_NGN_PER_KWH": "68.00"}):
        mock_model.predict.return_value = mock_df
        result = forecast_7d()
    required = {"date", "predicted_wh", "predicted_kwh", "lower_wh", "upper_wh", "estimated_cost_ngn"}
    for row in result["forecast"]:
        assert required.issubset(row.keys())
```

Confirm it fails.

---

### Step 3 — failing test: predicted_kwh derived from predicted_wh

**Test** (`tests/test_forecast.py`):
```python
def test_forecast_7d_predicted_kwh_equals_wh_over_1000():
    from src.model.forecast import forecast_7d
    mock_df = _make_mock_prophet_output()
    with patch("src.model.forecast._model") as mock_model, \
         patch.dict("os.environ", {"ELECTRICITY_TARIFF_NGN_PER_KWH": "68.00"}):
        mock_model.predict.return_value = mock_df
        result = forecast_7d()
    for row in result["forecast"]:
        assert row["predicted_kwh"] == pytest.approx(row["predicted_wh"] / 1000, rel=1e-5)
```

Confirm it fails.

---

### Step 4 — failing test: peak_day and lowest_day are correct

**Test** (`tests/test_forecast.py`):
```python
def test_forecast_7d_peak_and_lowest_day_correct():
    from src.model.forecast import forecast_7d
    mock_df = _make_mock_prophet_output()
    # Row 6 has highest yhat (6600.0), row 0 has lowest yhat (6000.0)
    with patch("src.model.forecast._model") as mock_model, \
         patch.dict("os.environ", {"ELECTRICITY_TARIFF_NGN_PER_KWH": "68.00"}):
        mock_model.predict.return_value = mock_df
        result = forecast_7d()
    from datetime import date, timedelta
    today = date.today()
    assert result["peak_day"] == (today + timedelta(days=6)).strftime("%A")
    assert result["lowest_day"] == today.strftime("%A")
```

Confirm it fails.

---

### Step 5 — implement `forecast_7d` in `src/model/forecast.py`

Add to the existing `forecast.py` after the singleton loader:

```python
import os
from datetime import date, timedelta
import pandas as pd

def forecast_7d() -> dict:
    tariff = float(os.environ["ELECTRICITY_TARIFF_NGN_PER_KWH"])
    today = date.today()
    future = pd.DataFrame(
        {"ds": pd.date_range(start=str(today), periods=7, freq="D")}
    )
    raw = _model.predict(future)
    rows = raw[["ds", "yhat", "yhat_lower", "yhat_upper"]].head(7)

    forecast = []
    for _, r in rows.iterrows():
        wh = float(r["yhat"])
        kwh = round(wh / 1000, 6)
        forecast.append({
            "date": r["ds"].strftime("%Y-%m-%d"),
            "predicted_wh": wh,
            "predicted_kwh": kwh,
            "lower_wh": float(r["yhat_lower"]),
            "upper_wh": float(r["yhat_upper"]),
            "estimated_cost_ngn": round(kwh * tariff, 2),
        })

    peak_idx = max(range(7), key=lambda i: forecast[i]["predicted_wh"])
    low_idx = min(range(7), key=lambda i: forecast[i]["predicted_wh"])

    return {
        "forecast": forecast,
        "peak_day": (today + timedelta(days=peak_idx)).strftime("%A"),
        "lowest_day": (today + timedelta(days=low_idx)).strftime("%A"),
    }
```

Run all four tests — all must pass.

---

## Git

- **Branch:** `feat/008-forecast-7d-function`
- **Commit format:** `feat(forecast): implement forecast_7d returning 7-day daily predictions`
- **PR title:** `feat(forecast): forecast_7d — 7-day daily prediction with peak/lowest day`
