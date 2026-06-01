---
epic: E2-smart-home-dashboard
feature: F4
issue: 005
slug: predictions-since-param
depends-on: 002-get-predictions-api-route, 001-get-predictions-db-function
---

# 005 — Extend GET /api/v1/predictions with `since` query param

## Goal

As a Smart Home homeowner, I can request only predictions from the last 24 hours so the chart and table load only relevant data.

## User Story

As a Smart Home homeowner, I want the predictions API to accept a `since` datetime filter so the dashboard can fetch only the last 24 hours of readings without pulling the full history.

## Reference Docs

- `docs/api-contracts.md` — GET /api/v1/predictions query params and response shape
- `docs/schema.md` — predictions table columns, `created_at` field

## Acceptance Criteria

- [ ] `GET /api/v1/predictions?since=2026-05-31T10:00:00Z` returns only rows where `created_at >= 2026-05-31T10:00:00Z`
- [ ] `GET /api/v1/predictions` with no `since` param returns all rows (existing behaviour unchanged)
- [ ] `since` can be combined with `tier` and `limit` params in the same request
- [ ] An invalid `since` value (not parseable as ISO datetime) returns HTTP 422
- [ ] `get_predictions(since="2026-05-31T10:00:00Z")` in `src/services/database.py` applies `.gte("created_at", "2026-05-31T10:00:00Z")` to the Supabase query chain
- [ ] `get_predictions(since=None)` does NOT add a `.gte` filter to the query chain

## Files to Modify

- `src/services/database.py`
- `src/api/routes.py`
- `tests/test_database.py`
- `tests/test_api.py`

## Out of Scope

- `until` / `before` upper-bound param
- Timezone conversion — caller must supply a UTC ISO 8601 string
- Pagination cursors

## Implementation Plan

### Step 1 — failing test: `.gte` called when `since` is provided

**Test file:** `tests/test_database.py`

```python
def test_get_predictions_since_applies_gte(mock_supabase):
    (mock_supabase.table.return_value.select.return_value
        .order.return_value.gte.return_value
        .limit.return_value.execute.return_value.data) = []
    get_predictions(since="2026-05-31T10:00:00Z")
    (mock_supabase.table.return_value.select.return_value
        .order.return_value.gte
        .assert_called_once_with("created_at", "2026-05-31T10:00:00Z"))
```

- `mock_supabase` patches `src.services.database.supabase`
- Import: `from src.services.database import get_predictions`
- Run pytest — confirm failure (`get_predictions` does not yet accept `since`)

### Step 2 — failing test: `.gte` NOT called when `since` is None

**Test file:** `tests/test_database.py`

```python
def test_get_predictions_no_gte_when_since_is_none(mock_supabase):
    (mock_supabase.table.return_value.select.return_value
        .order.return_value.limit.return_value.execute.return_value.data) = []
    get_predictions(since=None)
    (mock_supabase.table.return_value.select.return_value
        .order.return_value.gte.assert_not_called())
```

- Run pytest — confirm failure

### Step 3 — implement `since` in `get_predictions`

**File:** `src/services/database.py`

```python
def get_predictions(tier: str | None = None, limit: int = 20, since: str | None = None):
    query = supabase.table("predictions").select("*").order("created_at", desc=True)
    if since is not None:
        query = query.gte("created_at", since)
    if tier is not None:
        query = query.eq("tier", tier)
    return query.limit(limit).execute().data
```

- Run Steps 1 and 2 tests — both must pass before continuing

### Step 4 — failing test: route forwards `since` to `get_predictions`

**Test file:** `tests/test_api.py`

```python
def test_get_predictions_since_forwarded(client, mock_get_predictions):
    mock_get_predictions.return_value = []
    response = client.get("/api/v1/predictions?since=2026-05-31T10%3A00%3A00Z")
    assert response.status_code == 200
    mock_get_predictions.assert_called_once_with(
        tier=None, limit=20, since="2026-05-31T10:00:00+00:00"
    )
```

- `mock_get_predictions` patches `src.services.database.get_predictions`
- FastAPI parses the datetime and re-serialises it — match the exact isoformat string FastAPI emits
- Run pytest — confirm failure (route does not yet accept `since`)

### Step 5 — failing test: omitted `since` forwarded as None

**Test file:** `tests/test_api.py`

```python
def test_get_predictions_since_default_none(client, mock_get_predictions):
    mock_get_predictions.return_value = []
    response = client.get("/api/v1/predictions")
    assert response.status_code == 200
    mock_get_predictions.assert_called_once_with(tier=None, limit=20, since=None)
```

- Run pytest — confirm failure

### Step 6 — failing test: invalid `since` returns 422

**Test file:** `tests/test_api.py`

```python
def test_get_predictions_invalid_since_returns_422(client):
    response = client.get("/api/v1/predictions?since=not-a-date")
    assert response.status_code == 422
```

- Run pytest — confirm failure

### Step 7 — implement `since` param in the route

**File:** `src/api/routes.py`

```python
from datetime import datetime

@router.get("/predictions")
def get_predictions_route(
    tier: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=50),
    since: datetime | None = Query(default=None),
):
    since_str = since.isoformat() if since is not None else None
    return database.get_predictions(tier=tier, limit=limit, since=since_str)
```

- FastAPI validates `since` as ISO datetime — invalid string produces 422 automatically
- Run all 4 new tests plus the existing GET /predictions tests — all must pass

## Git

- **Branch:** `feat/005-predictions-since-param`
- **Commit format:** `feat(api): add since query param to GET /api/v1/predictions`
- **PR title:** `feat: filter predictions by datetime range (F4)`
