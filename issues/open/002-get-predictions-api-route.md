---
epic: E1-instant-appliance-prediction
feature: F3
issue: 002
slug: get-predictions-api-route
depends-on: 001
---

# 002 — GET /api/v1/predictions route

## Goal

As a homeowner, I can call GET /api/v1/predictions to receive my prediction history as JSON.

## User Story

As a homeowner, I want an API endpoint that returns my stored predictions so the frontend can display them without me navigating away.

## Reference Docs

- `docs/api-contracts.md` — GET /api/v1/predictions query params and response shape
- `docs/schema.md` — predictions table columns

## Acceptance Criteria

- [ ] `GET /api/v1/predictions` returns HTTP 200 with a JSON array
- [ ] `GET /api/v1/predictions?tier=simple` returns only rows where `tier == "simple"`
- [ ] `GET /api/v1/predictions?tier=full` returns only rows where `tier == "full"`
- [ ] `GET /api/v1/predictions?limit=5` returns at most 5 rows
- [ ] `GET /api/v1/predictions?limit=100` is capped at 50 (returns 422 or clamps — see plan)
- [ ] Default limit is 20 when param is omitted (matches api-contracts.md spec)
- [ ] Response items contain: `id`, `tier`, `predicted_wh`, `predicted_kwh`, `estimated_cost_ngn`, `location`, `created_at`
- [ ] Empty list `[]` is a valid 200 response when no predictions exist

## Files to Modify

- `src/api/routes.py`
- `tests/test_api.py`

## Out of Scope

- Authentication or per-user filtering
- Pagination cursors
- History for any tier other than what the `tier` param requests
- Deleting or modifying predictions via this route

## Implementation Plan

### Step 1 — failing test: 200 with list

**Test file:** `tests/test_api.py`

```python
def test_get_predictions_returns_200(client, mock_get_predictions):
    mock_get_predictions.return_value = []
    response = client.get("/api/v1/predictions")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
```

- `client` is the FastAPI TestClient fixture
- `mock_get_predictions` patches `src.services.database.get_predictions`
- Run pytest — confirm 404 (route not registered yet)

### Step 2 — failing test: tier query param forwarded

**Test file:** `tests/test_api.py`

```python
def test_get_predictions_tier_filter(client, mock_get_predictions):
    mock_get_predictions.return_value = [
        {"id": "a", "tier": "simple", "predicted_wh": 60.0, "predicted_kwh": 0.06,
         "estimated_cost_ngn": 4.08, "location": "Lagos", "created_at": "2026-06-01T10:00:00Z"}
    ]
    response = client.get("/api/v1/predictions?tier=simple")
    assert response.status_code == 200
    mock_get_predictions.assert_called_once_with(tier="simple", limit=20)
```

- Run pytest — confirm failure

### Step 3 — failing test: limit query param forwarded

**Test file:** `tests/test_api.py`

```python
def test_get_predictions_limit_param(client, mock_get_predictions):
    mock_get_predictions.return_value = []
    response = client.get("/api/v1/predictions?limit=5")
    assert response.status_code == 200
    mock_get_predictions.assert_called_once_with(tier=None, limit=5)
```

- Run pytest — confirm failure

### Step 4 — failing test: limit capped at 50

**Test file:** `tests/test_api.py`

```python
def test_get_predictions_limit_max_50(client, mock_get_predictions):
    mock_get_predictions.return_value = []
    response = client.get("/api/v1/predictions?limit=100")
    assert response.status_code == 422
```

- Pydantic `Query(le=50)` will produce 422 automatically — no custom error handling needed
- Run pytest — confirm failure

### Step 5 — failing test: response items have required fields

**Test file:** `tests/test_api.py`

```python
def test_get_predictions_response_shape(client, mock_get_predictions):
    mock_get_predictions.return_value = [
        {"id": "uuid-1", "tier": "simple", "predicted_wh": 60.5,
         "predicted_kwh": 0.0605, "estimated_cost_ngn": 4.11,
         "location": "Lagos", "created_at": "2026-06-01T10:00:00Z"}
    ]
    response = client.get("/api/v1/predictions")
    item = response.json()[0]
    assert set(item.keys()) == {"id", "tier", "predicted_wh", "predicted_kwh",
                                 "estimated_cost_ngn", "location", "created_at"}
```

- Run pytest — confirm failure

### Step 6 — implement the route

**File:** `src/api/routes.py`

```python
from fastapi import Query

@router.get("/predictions")
def get_predictions_route(
    tier: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=50),
):
    return database.get_predictions(tier=tier, limit=limit)
```

- Run all 5 tests — all must pass

## Git

- **Branch:** `feat/002-get-predictions-api-route`
- **Commit format:** `feat(api): add GET /api/v1/predictions with tier and limit params`
- **PR title:** `feat: add GET /api/v1/predictions endpoint (F3)`
