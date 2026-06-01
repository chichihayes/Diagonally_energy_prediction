---
epic: E5-monitoring-and-retraining
feature: F2
slug: add-get-monitor-drift-endpoint
---

# 015 — Add GET /api/v1/monitor/drift Endpoint

## Goal

As a system operator, I want to query the latest drift check result via HTTP so I can monitor distribution shift over time without accessing Supabase directly.

## User Story

As a system operator, I want `GET /api/v1/monitor/drift` to return the most recent row from `drift_log`, including which features drifted and their deviation percentages, so I can audit drift events through a simple API call.

## Reference Docs

- `docs/api-contracts.md` — route conventions, error codes, response shapes
- `docs/schema.md` — `drift_log` table columns (added in Issue 013)

## Acceptance Criteria

- [ ] `GET /api/v1/monitor/drift` returns 200 and the latest drift event when one exists
- [ ] Response shape: `{"timestamp": str, "drift_detected": bool, "drifted_features": list[str], "deviations": dict[str, float], "clean_row_count": int}`
- [ ] Returns 404 with `{"detail": "No drift check has been run yet"}` when `drift_log` is empty
- [ ] Returns 500 if `get_latest_drift_event` raises an exception
- [ ] Route is registered under the `/api/v1` prefix (consistent with all other routes)
- [ ] New endpoint is documented in `docs/api-contracts.md`

## Files to Modify

- `src/api/routes.py` — add the route
- `docs/api-contracts.md` — add `GET /api/v1/monitor/drift` section
- `tests/test_api.py` — add tests (write first, confirm they fail, then implement)

## Out of Scope

- Authentication or rate limiting
- Historical drift log (only the single latest row)
- Frontend display of drift status
- Drift history pagination

## Implementation Plan

### Step 1 — Write failing tests in `tests/test_api.py`

**Test:** `test_get_monitor_drift_returns_200_with_latest_event`
- Patch `database.get_latest_drift_event` to return:
  `{"timestamp": "2026-06-01T10:00:00Z", "drift_detected": True, "drifted_features": ["T1"], "deviations": {"T1": 20.5}, "clean_row_count": 100}`
- `GET /api/v1/monitor/drift` via `TestClient`
- Assert: `response.status_code == 200`
- Assert: `response.json()["drift_detected"] == True`
- Assert: `response.json()["drifted_features"] == ["T1"]`
- Assert: `response.json()["deviations"]["T1"] == 20.5`
- Assert: `response.json()["clean_row_count"] == 100`

**Test:** `test_get_monitor_drift_returns_404_when_no_data`
- Patch `database.get_latest_drift_event` to return `None`
- `GET /api/v1/monitor/drift`
- Assert: `response.status_code == 404`
- Assert: `response.json()["detail"] == "No drift check has been run yet"`

**Test:** `test_get_monitor_drift_returns_500_on_db_error`
- Patch `database.get_latest_drift_event` to raise `Exception("db connection failed")`
- `GET /api/v1/monitor/drift`
- Assert: `response.status_code == 500`

### Step 2 — Document endpoint in `docs/api-contracts.md`

Add the following section after `GET /health`:

```
## GET /api/v1/monitor/drift

Returns the most recent drift check result from the drift_log table.

**Response — 200:**
{
  "timestamp": "2026-06-01T10:00:00Z",
  "drift_detected": true,
  "drifted_features": ["T1", "RH_2"],
  "deviations": {"T1": 20.5, "RH_2": 16.1, ...},
  "clean_row_count": 100
}

**Errors:**
| Code | Meaning |
|---|---|
| 404  | No drift check has been run yet |
| 500  | Failed to retrieve drift status from database |
```

### Step 3 — Implement the route in `src/api/routes.py`

```python
@router.get("/monitor/drift")
def get_drift_status():
    try:
        event = database.get_latest_drift_event()
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to retrieve drift status")
    if event is None:
        raise HTTPException(status_code=404, detail="No drift check has been run yet")
    return event
```

### Step 4 — Confirm all 3 tests pass

Run `pytest tests/test_api.py -v -k drift` and verify green.

## Git

- Branch: `feat/E5-F2-monitor-drift-endpoint`
- Commit: `feat(api): add GET /api/v1/monitor/drift endpoint returning latest drift check`
- PR: `feat: Add GET /api/v1/monitor/drift — expose latest drift status via API`
