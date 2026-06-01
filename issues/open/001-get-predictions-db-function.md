---
epic: E1-instant-appliance-prediction
feature: F3
issue: 001
slug: get-predictions-db-function
---

# 001 — get_predictions() database function

## Goal

As a homeowner, my prediction history can be retrieved from Supabase so the API can return it.

## User Story

As a homeowner, I want the system to fetch my stored predictions from the database so that the API can serve them to any frontend that asks.

## Reference Docs

- `docs/schema.md` — predictions table columns and types
- `docs/api-contracts.md` — GET /api/v1/predictions response shape

## Acceptance Criteria

- [ ] `get_predictions()` with no arguments returns a list of dicts (may be empty)
- [ ] `get_predictions(tier="simple")` returns only rows where `tier == "simple"`
- [ ] `get_predictions(tier="full")` returns only rows where `tier == "full"`
- [ ] `get_predictions(limit=3)` returns at most 3 rows
- [ ] Default limit is 10 when `limit` is not passed
- [ ] Rows are ordered by `created_at` descending (most recent first)
- [ ] Each returned dict contains: `id`, `tier`, `predicted_wh`, `predicted_kwh`, `estimated_cost_ngn`, `location`, `created_at`
- [ ] Function raises no exception when the table is empty

## Files to Modify

- `src/services/database.py`
- `tests/test_database.py`

## Out of Scope

- Pagination beyond the limit param
- Filtering by date range
- Returning `inputs` (raw feature JSON) — not needed by the history table
- Any write operations

## Implementation Plan

### Step 1 — failing test: returns a list

**Test file:** `tests/test_database.py`

```python
def test_get_predictions_returns_list(mock_supabase):
    result = get_predictions()
    assert isinstance(result, list)
```

- Mock `supabase.table("predictions").select("*").order(...).limit(...).execute()` to return an object with `.data = []`
- Run pytest — confirm `ImportError` or `AttributeError` (function does not exist yet)

### Step 2 — failing test: tier filter

**Test file:** `tests/test_database.py`

```python
def test_get_predictions_filters_by_tier(mock_supabase):
    mock_supabase.return_value = [
        {"id": "a", "tier": "simple", "predicted_wh": 60.0, "predicted_kwh": 0.06,
         "estimated_cost_ngn": 4.08, "location": "Lagos", "created_at": "2026-06-01T10:00:00Z"},
        {"id": "b", "tier": "full", "predicted_wh": 84.0, "predicted_kwh": 0.084,
         "estimated_cost_ngn": 5.71, "location": "Lagos", "created_at": "2026-06-01T09:00:00Z"},
    ]
    result = get_predictions(tier="simple")
    assert all(row["tier"] == "simple" for row in result)
```

- Run pytest — confirm test fails (function missing)

### Step 3 — failing test: limit respected

**Test file:** `tests/test_database.py`

```python
def test_get_predictions_respects_limit(mock_supabase_with_5_rows):
    result = get_predictions(limit=3)
    assert len(result) <= 3
```

- Mock returns 5 rows; Supabase `.limit(3)` should cap it
- Run pytest — confirm failure

### Step 4 — failing test: default limit is 10

**Test file:** `tests/test_database.py`

```python
def test_get_predictions_default_limit_is_10(mock_supabase, capture_limit):
    get_predictions()
    capture_limit.assert_called_with(10)
```

- Spy on the `.limit()` call to verify the value passed
- Run pytest — confirm failure

### Step 5 — implement `get_predictions`

**File:** `src/services/database.py`

```python
def get_predictions(tier: str | None = None, limit: int = 10) -> list[dict]:
    query = (
        supabase.table("predictions")
        .select("id, tier, predicted_wh, predicted_kwh, estimated_cost_ngn, location, created_at")
        .order("created_at", desc=True)
        .limit(limit)
    )
    if tier is not None:
        query = query.eq("tier", tier)
    response = query.execute()
    return response.data
```

- Run all 4 tests — all must pass

## Git

- **Branch:** `feat/001-get-predictions-db-function`
- **Commit format:** `feat(database): add get_predictions() with tier filter and limit`
- **PR title:** `feat: add get_predictions() database function (F3)`
