---
epic: E5-monitoring-and-retraining
feature: F2
slug: create-drift-log-schema-and-db-functions
---

# 013 — Add drift_log Schema and Supabase Persistence Functions

## Goal

As a system operator, I want every drift check to be persisted to Supabase so I have a complete audit trail — including checks where no drift was found — and can query the latest result via the API.

## User Story

As a system operator, I want `store_drift_event` to insert one row per drift check and `get_latest_drift_event` to return the most recent row, so the drift endpoint always reflects the most recent state.

## Reference Docs

- `docs/schema.md` — Supabase tables section (follow existing table format)
- `docs/architecture.md` — service boundaries; database.py is the only file that touches Supabase

## Acceptance Criteria

- [ ] `drift_log` table schema documented in `docs/schema.md` with columns: `id (uuid, PK)`, `timestamp (timestamptz)`, `drift_detected (bool)`, `drifted_features (text[])`, `deviations (JSONB)`, `clean_row_count (int)`
- [ ] `store_drift_event(record: dict) -> None` inserts one row regardless of whether `drift_detected` is `True` or `False`
- [ ] `get_latest_drift_event() -> dict | None` returns the most recent row ordered by `timestamp desc`, or `None` when the table is empty
- [ ] Both functions use `supabase-py` client — never raw psycopg2
- [ ] `store_drift_event` propagates Supabase client exceptions upward (does not silently swallow errors)

## Files to Modify

- `docs/schema.md` — add `## Supabase — drift_log table` section
- `src/services/database.py` — add `store_drift_event` and `get_latest_drift_event`
- `tests/test_database.py` — add tests (write first, confirm they fail, then implement)

## Out of Scope

- Creating the table in the Supabase dashboard (schema doc is the spec; table creation is a manual step)
- Scheduler wiring (Issue 014)
- API endpoint (Issue 015)

## Implementation Plan

### Step 1 — Write failing tests in `tests/test_database.py`

**Test:** `test_store_drift_event_calls_supabase_insert`
- Patch the supabase client so `table('drift_log').insert({...}).execute()` is mocked
- Call `store_drift_event({"timestamp": "2026-06-01T10:00:00Z", "drift_detected": True, "drifted_features": ["T1"], "deviations": {"T1": 20.0}, "clean_row_count": 100})`
- Assert: the mocked `insert` was called once
- Assert: the dict passed to `insert` contains `"drift_detected": True` and `"drifted_features": ["T1"]`

**Test:** `test_store_drift_event_inserts_even_when_no_drift`
- Call `store_drift_event({"timestamp": "2026-06-01T10:00:00Z", "drift_detected": False, "drifted_features": [], "deviations": {}, "clean_row_count": 100})`
- Assert: the mocked `insert` was called once (audit trail requires every check to be stored)

**Test:** `test_get_latest_drift_event_returns_most_recent_row`
- Mock `table('drift_log').select('*').order('timestamp', desc=True).limit(1).execute()` to return data `[{"id": "abc", "timestamp": "2026-06-01T10:00:00Z", "drift_detected": True, "drifted_features": ["T1"], "deviations": {"T1": 20.0}, "clean_row_count": 100}]`
- Call `get_latest_drift_event()`
- Assert: return value equals that dict

**Test:** `test_get_latest_drift_event_returns_none_when_empty`
- Mock `.execute()` to return data `[]`
- Call `get_latest_drift_event()`
- Assert: return value is `None`

### Step 2 — Update `docs/schema.md`

Add the following section after the existing Supabase tables:

```
## Supabase — drift_log table

| Column           | Type        | Notes                                      |
|---|---|---|
| id               | uuid        | Primary key, auto-generated                |
| timestamp        | timestamptz | Auto-set on insert                         |
| drift_detected   | bool        | True if any feature exceeded 15% deviation |
| drifted_features | text[]      | Feature names that exceeded threshold      |
| deviations       | jsonb       | Feature → deviation_pct for all 25 features|
| clean_row_count  | int         | Number of clean readings in this window    |
```

### Step 3 — Implement database functions in `src/services/database.py`

```python
def store_drift_event(record: dict) -> None:
    supabase.table('drift_log').insert(record).execute()

def get_latest_drift_event() -> dict | None:
    result = supabase.table('drift_log').select('*').order('timestamp', desc=True).limit(1).execute()
    return result.data[0] if result.data else None
```

### Step 4 — Confirm all 4 tests pass

Run `pytest tests/test_database.py -v -k drift` and verify green.

## Git

- Branch: `feat/E5-F2-drift-log-db`
- Commit: `feat(database): add store_drift_event and get_latest_drift_event for drift_log`
- PR: `feat: Add drift_log schema and Supabase persistence functions`
