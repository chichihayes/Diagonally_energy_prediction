---
id: "010"
slug: implement-forecast-24h-endpoint
feature: F1
epic: E3
title: Implement GET /api/v1/forecast/24h route
status: open
---

# 010 — Implement GET /api/v1/forecast/24h route

## Goal

`GET /api/v1/forecast/24h?location=Lagos` exists in `routes.py`, calls
`forecast_24h()` from `forecast.py`, maps the returned dicts to the API
response shape defined in `docs/api-contracts.md`, computes `peak_hour` and
`lowest_hour`, and returns within 2 seconds.

## User Story

As a frontend developer building the forecast chart, I want
`GET /api/v1/forecast/24h?location=Lagos` to return a 24-element forecast
array with `peak_hour` and `lowest_hour` callouts so I can render the chart
without writing any model or cost logic in the browser.

## Reference Docs

- `docs/api-contracts.md` — GET /api/v1/forecast/24h: query params, exact response shape, error codes
- `docs/architecture.md` — service boundaries: route validates input and calls services; no business logic in the route
- `CLAUDE.md` — error handling: raise HTTPException with correct status code; 400 for bad input, 500 for model/weather errors

## Acceptance Criteria

- [ ] Route is registered at `GET /api/v1/forecast/24h` in `routes.py`
- [ ] Missing `location` query param returns `400` (not FastAPI's default 422 — make `location` optional with `None` default and raise manually)
- [ ] Valid `location` returns `200` with body: `{ "forecast": [...], "peak_hour": str, "lowest_hour": str }`
- [ ] Each `forecast` item contains exactly: `hour`, `predicted_wh`, `predicted_kwh`, `lower_wh`, `upper_wh`, `estimated_cost_ngn`
- [ ] `hour` maps from `forecast_24h` output field `ds`
- [ ] `predicted_wh` maps from `yhat`, `lower_wh` from `yhat_lower`, `upper_wh` from `yhat_upper`
- [ ] `peak_hour` is the `hour` value of the item with the highest `predicted_wh`
- [ ] `lowest_hour` is the `hour` value of the item with the lowest `predicted_wh`
- [ ] Any exception from `forecast_24h()` is caught and re-raised as `HTTPException(status_code=500)`

## Files to Modify

- `src/api/routes.py` — add `GET /api/v1/forecast/24h` handler

> Do not modify `forecast.py`, `cost.py`, or any test file. Tests are issue 011.

## Out of Scope

- 7-day forecast endpoint `/api/v1/forecast/7d` (F2)
- `forecast.html` frontend (F3)
- Model leaderboard endpoint (F4)
- Saving forecast results to Supabase

## Implementation Plan

### Step 1 — Add the route handler to routes.py

The route converts `forecast_24h()` output to the API response shape.
`forecast_24h()` returns dicts with keys: `ds, yhat, yhat_lower, yhat_upper, predicted_kwh, estimated_cost_ngn`.
The route renames these to: `hour, predicted_wh, lower_wh, upper_wh, predicted_kwh, estimated_cost_ngn`.

`location` must be declared `Optional[str] = None` (not `Query(...)`) so FastAPI does not
emit a 422 — the handler raises 400 manually when `location` is None.

**Test** (written in issue 011 — route handler must pass those tests):

The implementation must satisfy:
- `client.get("/api/v1/forecast/24h?location=Lagos")` → 200
- `client.get("/api/v1/forecast/24h")` → 400
- A patched `forecast_24h` that raises `RuntimeError` → 500

**File:** `src/api/routes.py` — add:

```python
from typing import Optional
from src.model.forecast import forecast_24h as _forecast_24h

@router.get("/forecast/24h")
async def get_forecast_24h(location: Optional[str] = None):
    if not location:
        raise HTTPException(status_code=400, detail="location is required")
    try:
        raw = _forecast_24h(location)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    items = [
        {
            "hour": entry["ds"],
            "predicted_wh": entry["yhat"],
            "predicted_kwh": entry["predicted_kwh"],
            "lower_wh": entry["yhat_lower"],
            "upper_wh": entry["yhat_upper"],
            "estimated_cost_ngn": entry["estimated_cost_ngn"],
        }
        for entry in raw
    ]

    peak_hour = max(items, key=lambda x: x["predicted_wh"])["hour"]
    lowest_hour = min(items, key=lambda x: x["predicted_wh"])["hour"]

    return {"forecast": items, "peak_hour": peak_hour, "lowest_hour": lowest_hour}
```

## Git

- **Branch:** `feat/010-implement-forecast-24h-endpoint`
- **Commit format:** `feat(api): implement GET /api/v1/forecast/24h with peak_hour and lowest_hour`
- **PR title:** `feat(api): add GET /api/v1/forecast/24h endpoint`
