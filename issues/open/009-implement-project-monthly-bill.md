---
id: "009"
slug: implement-project-monthly-bill
feature: F2
epic: E3
title: Implement project_monthly_bill in src/services/cost.py
status: open
---

# 009 — Implement `project_monthly_bill` in `src/services/cost.py`

## Goal

`project_monthly_bill(forecast)` scales a 7-day forecast array to a 30-day
window and returns three NGN values — optimistic, most likely, pessimistic —
so the API can tell a homeowner how much their bill will likely be this month.

## User Story

As a homeowner planning ahead, I want a projected monthly bill shown as a low,
expected, and high range in Naira so I can decide whether to cut my appliance
usage before the bill arrives.

## Reference Docs

- `docs/schema.md` — Forecast Output Schema (yhat_lower → optimistic,
  yhat → most_likely, yhat_upper → pessimistic)
- `docs/api-contracts.md` — projected_month_bill shape in GET /api/v1/forecast/7d
- `CLAUDE.md` — Layer 3 Bill Estimation conventions (formula, rounding, env var)

## Acceptance Criteria

- [ ] `project_monthly_bill(forecast)` accepts a list of 7 forecast dicts, each containing `predicted_wh`, `lower_wh`, `upper_wh`
- [ ] Returns a dict with exactly three keys: `optimistic_ngn`, `most_likely_ngn`, `pessimistic_ngn`
- [ ] `optimistic_ngn = round(sum(lower_wh) / 1000 * (30/7) * tariff, 2)`
- [ ] `most_likely_ngn = round(sum(predicted_wh) / 1000 * (30/7) * tariff, 2)`
- [ ] `pessimistic_ngn = round(sum(upper_wh) / 1000 * (30/7) * tariff, 2)`
- [ ] Tariff always read from `ELECTRICITY_TARIFF_NGN_PER_KWH` env var — never hardcoded
- [ ] All three values are rounded to 2 decimal places
- [ ] `optimistic_ngn <= most_likely_ngn <= pessimistic_ngn` for any valid input

## Files to Modify

- `src/services/cost.py` — add `project_monthly_bill(forecast)` alongside the existing cost functions

## Out of Scope

- GET /api/v1/forecast/7d route (issue 010)
- `forecast_7d` function in forecast.py (issue 008)
- Per-homeowner tariff input — rate comes from env var only
- Monthly bill from 24-hour forecast

## Implementation Plan

### Step 1 — failing test: function returns a dict with correct keys

**Test** (`tests/test_cost.py`):
```python
import pytest
from unittest.mock import patch

_MOCK_FORECAST = [
    {"predicted_wh": 6000.0, "lower_wh": 4000.0, "upper_wh": 8000.0},
    {"predicted_wh": 6100.0, "lower_wh": 4100.0, "upper_wh": 8100.0},
    {"predicted_wh": 6200.0, "lower_wh": 4200.0, "upper_wh": 8200.0},
    {"predicted_wh": 6300.0, "lower_wh": 4300.0, "upper_wh": 8300.0},
    {"predicted_wh": 6400.0, "lower_wh": 4400.0, "upper_wh": 8400.0},
    {"predicted_wh": 6500.0, "lower_wh": 4500.0, "upper_wh": 8500.0},
    {"predicted_wh": 6600.0, "lower_wh": 4600.0, "upper_wh": 8600.0},
]

def test_project_monthly_bill_returns_correct_keys():
    from src.services.cost import project_monthly_bill
    with patch.dict("os.environ", {"ELECTRICITY_TARIFF_NGN_PER_KWH": "68.00"}):
        result = project_monthly_bill(_MOCK_FORECAST)
    assert set(result.keys()) == {"optimistic_ngn", "most_likely_ngn", "pessimistic_ngn"}
```

Confirm it fails (`ImportError` — `project_monthly_bill` does not exist yet).

---

### Step 2 — failing test: optimistic_ngn value is correct

**Test** (`tests/test_cost.py`):
```python
def test_project_monthly_bill_optimistic_ngn_correct():
    from src.services.cost import project_monthly_bill
    # sum(lower_wh) = 4000+4100+4200+4300+4400+4500+4600 = 29100 Wh = 29.1 kWh
    # scaled: 29.1 * (30/7) = 124.71... kWh
    # optimistic_ngn = round(124.71... * 68.00, 2) = round(8480.57..., 2) = 8480.57
    with patch.dict("os.environ", {"ELECTRICITY_TARIFF_NGN_PER_KWH": "68.00"}):
        result = project_monthly_bill(_MOCK_FORECAST)
    expected = round(sum(r["lower_wh"] for r in _MOCK_FORECAST) / 1000 * (30 / 7) * 68.00, 2)
    assert result["optimistic_ngn"] == pytest.approx(expected, abs=0.01)
```

Confirm it fails.

---

### Step 3 — failing test: most_likely_ngn value is correct

**Test** (`tests/test_cost.py`):
```python
def test_project_monthly_bill_most_likely_ngn_correct():
    from src.services.cost import project_monthly_bill
    # sum(predicted_wh) = 6000+6100+...+6600 = 43400 Wh = 43.4 kWh
    # scaled: 43.4 * (30/7) = 185.71... kWh
    # most_likely_ngn = round(185.71... * 68.00, 2) = round(12628.57..., 2) = 12628.57
    with patch.dict("os.environ", {"ELECTRICITY_TARIFF_NGN_PER_KWH": "68.00"}):
        result = project_monthly_bill(_MOCK_FORECAST)
    expected = round(sum(r["predicted_wh"] for r in _MOCK_FORECAST) / 1000 * (30 / 7) * 68.00, 2)
    assert result["most_likely_ngn"] == pytest.approx(expected, abs=0.01)
```

Confirm it fails.

---

### Step 4 — failing test: pessimistic_ngn value is correct and ordering holds

**Test** (`tests/test_cost.py`):
```python
def test_project_monthly_bill_pessimistic_ngn_correct_and_ordering():
    from src.services.cost import project_monthly_bill
    with patch.dict("os.environ", {"ELECTRICITY_TARIFF_NGN_PER_KWH": "68.00"}):
        result = project_monthly_bill(_MOCK_FORECAST)
    expected = round(sum(r["upper_wh"] for r in _MOCK_FORECAST) / 1000 * (30 / 7) * 68.00, 2)
    assert result["pessimistic_ngn"] == pytest.approx(expected, abs=0.01)
    assert result["optimistic_ngn"] <= result["most_likely_ngn"] <= result["pessimistic_ngn"]
```

Confirm it fails.

---

### Step 5 — implement `project_monthly_bill` in `src/services/cost.py`

Add to the existing `cost.py` after the existing cost functions:

```python
import os

def project_monthly_bill(forecast: list[dict]) -> dict:
    tariff = float(os.environ["ELECTRICITY_TARIFF_NGN_PER_KWH"])
    scale = 30 / 7
    optimistic_ngn = round(
        sum(r["lower_wh"] for r in forecast) / 1000 * scale * tariff, 2
    )
    most_likely_ngn = round(
        sum(r["predicted_wh"] for r in forecast) / 1000 * scale * tariff, 2
    )
    pessimistic_ngn = round(
        sum(r["upper_wh"] for r in forecast) / 1000 * scale * tariff, 2
    )
    return {
        "optimistic_ngn": optimistic_ngn,
        "most_likely_ngn": most_likely_ngn,
        "pessimistic_ngn": pessimistic_ngn,
    }
```

Run all four tests — all must pass.

---

## Git

- **Branch:** `feat/009-project-monthly-bill`
- **Commit format:** `feat(cost): implement project_monthly_bill scaling 7-day forecast to 30-day NGN projection`
- **PR title:** `feat(cost): project_monthly_bill — 7-day to 30-day NGN bill projection`
