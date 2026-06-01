---
id: "014"
slug: store-anomaly-db
feature: F1
epic: E5
title: Add store_anomaly to database.py and anomalies table schema
status: open
---

# 014 — Add store_anomaly to database.py and anomalies table schema

## Goal

Flagged anomalous readings are persisted to a Supabase `anomalies` table so the
system has a complete audit trail of out-of-distribution sensor readings and
future retraining logic can correctly exclude them from the clean row pool.

## User Story

As the prediction route handler, I want `store_anomaly(record)` to write flagged
readings to Supabase so anomalous readings are recorded separately from clean
predictions and are never counted in the retraining pool.

## Reference Docs

- `docs/schema.md` — existing table definitions; anomalies table to be added here
- `CLAUDE.md` — database conventions: supabase-py client, RLS; anomalous readings
  must not count as clean rows and must never be inserted into the predictions table

## Acceptance Criteria

- [ ] `docs/schema.md` contains an `anomalies` table section with columns:
  `id (uuid)`, `timestamp (timestamptz)`, `tier (text)`,
  `input_features (jsonb)`, `z_scores (jsonb)`, `flagged_features (text[])`,
  `low_confidence_prediction (bool)`
- [ ] `store_anomaly(record: dict)` inserts one row into the `anomalies` table
- [ ] `store_anomaly` uses the existing `supabase` client already in `database.py` — no new client
- [ ] If the Supabase insert raises an exception, it propagates (not swallowed)
- [ ] Anomalous rows are never inserted into the `predictions` table
- [ ] Unit test mocks `supabase.table("anomalies").insert({}).execute()` and asserts
  it was called with the correct record shape

## Files to Modify

- `docs/schema.md` — add anomalies table section
- `src/services/database.py` — add `store_anomaly(record: dict) -> None`

## Out of Scope

- Calling `store_anomaly` from routes.py (issue 015)
- Creating the Supabase table — that is a manual migration step outside this codebase
- Querying anomalies (drift detection is F2)

## Implementation Plan

### Step 1 — update docs/schema.md

Append the following section to `docs/schema.md`:

```markdown
## Supabase — anomalies table

| Column | Type | Notes |
|---|---|---|
| id | uuid | Primary key, auto-generated |
| timestamp | timestamptz | Time the reading was flagged |
| tier | text | `'full'` or `'simple'` |
| input_features | jsonb | All feature values submitted to the model |
| z_scores | jsonb | Z-Score per feature (only features with std > 0) |
| flagged_features | text[] | Feature names where abs(Z) > 3 |
| low_confidence_prediction | bool | Always true for rows in this table |
```

---

### Step 2 — write failing test

**File:** `tests/test_database.py`

```python
def test_store_anomaly_calls_supabase_insert():
    from unittest.mock import MagicMock, patch
    from src.services.database import store_anomaly

    record = {
        "timestamp": "2026-06-01T10:00:00Z",
        "tier": "full",
        "input_features": {"T1": 999.0, "lights": 0},
        "z_scores": {"T1": 30.1},
        "flagged_features": ["T1"],
        "low_confidence_prediction": True,
    }

    mock_execute = MagicMock()
    mock_insert = MagicMock(return_value=MagicMock(execute=mock_execute))
    mock_table = MagicMock(return_value=MagicMock(insert=mock_insert))

    with patch("src.services.database.supabase") as mock_client:
        mock_client.table = mock_table
        store_anomaly(record)

    mock_table.assert_called_once_with("anomalies")
    mock_insert.assert_called_once_with(record)
    mock_execute.assert_called_once()
```

Confirm the test fails (`ImportError` or `AttributeError`) before implementing.

---

### Step 3 — implement store_anomaly

**File:** `src/services/database.py` — add the following function:

```python
def store_anomaly(record: dict) -> None:
    supabase.table("anomalies").insert(record).execute()
```

This mirrors the pattern of any existing `store_*` function already in the file.
Use the `supabase` client that is already initialised at module level.

Confirm the test passes.

## Git

- **Branch:** `feat/014-store-anomaly-db`
- **Commit format:** `feat(services): add store_anomaly to database.py, add anomalies table to schema.md`
- **PR title:** `feat(services): store flagged anomalies in Supabase anomalies table`
