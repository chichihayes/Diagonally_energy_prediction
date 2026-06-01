---
id: "015"
slug: add-retrain-status-api-endpoint
feature: F3
epic: E5
title: Add GET /api/v1/monitor/retrain endpoint
status: open
---

# 015 — Add `GET /api/v1/monitor/retrain` endpoint

## Goal

Expose a read-only endpoint that returns the most recent row from `retrain_log`
so a system operator can check whether the model has ever been retrained, whether
the replacement was accepted, and what R² improvement was achieved — without
querying Supabase directly.

## User Story

As a system operator, I want to hit a single URL and immediately see the outcome
of the last automatic retraining attempt so I can confirm the model is improving
and the pipeline is healthy.

## Reference Docs

- `docs/api-contracts.md` — add GET /api/v1/monitor/retrain contract here
- `docs/schema.md` — `retrain_log` schema (defined in issue 014)
- `CLAUDE.md` — Error handling: 404 when no rows exist, 500 on model error

## Acceptance Criteria

- [ ] `GET /api/v1/monitor/retrain` returns 200 with response shape `{"timestamp": str, "old_model_r2": float, "new_model_r2": float, "model_replaced": bool, "rows_used": int}` when a retrain_log row exists
- [ ] `GET /api/v1/monitor/retrain` returns 404 when `retrain_log` table is empty
- [ ] `test_retrain_status_returns_200_with_correct_shape` — mocked Supabase returns one `retrain_log` row; response is 200 with all five fields present
- [ ] `test_retrain_status_model_replaced_true_reflected_in_response` — when `retrain_log` row has `model_replaced=True`, response `model_replaced` is `True`
- [ ] `test_retrain_status_model_replaced_false_reflected_in_response` — when `retrain_log` row has `model_replaced=False`, response `model_replaced` is `False`
- [ ] `test_retrain_status_returns_404_when_no_rows` — mocked Supabase returns empty list; response is 404
- [ ] `test_retrain_status_returns_500_on_supabase_error` — mocked Supabase raises exception; response is 500
- [ ] GET /api/v1/monitor/retrain contract added to `docs/api-contracts.md`
- [ ] All tests pass without a real Supabase connection

## Files to Modify

- `src/api/routes.py` — add GET /api/v1/monitor/retrain route
- `docs/api-contracts.md` — add endpoint contract
- `tests/test_retrain_trigger.py` — add all 5 tests

## Out of Scope

- Pagination or filtering retrain_log history (first row only)
- Authentication or API key gating
- Listing multiple retraining runs
- Triggering retraining via POST (manual trigger not in scope for F3)

## Implementation Plan

### Step 1 — add contract to `docs/api-contracts.md`

Append under the monitoring section:

```
### GET /api/v1/monitor/retrain

Returns the most recent retraining outcome.

**Response 200:**
{
  "timestamp":     "2026-06-01T10:00:00+00:00",
  "old_model_r2":  0.75,
  "new_model_r2":  0.85,
  "model_replaced": true,
  "rows_used":     2500
}

**Response 404:** No retraining has ever run.
**Response 500:** Supabase query error.
```

---

### Step 2 — write all 5 failing tests

Add to `tests/test_retrain_trigger.py`:

```python
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock


_RETRAIN_LOG_ROW = {
    "timestamp": "2026-06-01T10:00:00+00:00",
    "old_model_r2": 0.75,
    "new_model_r2": 0.85,
    "model_replaced": True,
    "rows_used": 2500,
}

_RETRAIN_LOG_ROW_NOT_REPLACED = {**_RETRAIN_LOG_ROW, "model_replaced": False}


def _client():
    from src.api.main import app
    return TestClient(app)


def test_retrain_status_returns_200_with_correct_shape():
    mock_db = MagicMock()
    mock_db.table.return_value.select.return_value.order.return_value \
        .limit.return_value.execute.return_value.data = [_RETRAIN_LOG_ROW]
    with patch("src.api.routes.supabase", mock_db):
        response = _client().get("/api/v1/monitor/retrain")
    assert response.status_code == 200
    body = response.json()
    assert {"timestamp", "old_model_r2", "new_model_r2", "model_replaced", "rows_used"} \
        .issubset(body.keys())


def test_retrain_status_model_replaced_true_reflected_in_response():
    mock_db = MagicMock()
    mock_db.table.return_value.select.return_value.order.return_value \
        .limit.return_value.execute.return_value.data = [_RETRAIN_LOG_ROW]
    with patch("src.api.routes.supabase", mock_db):
        response = _client().get("/api/v1/monitor/retrain")
    assert response.json()["model_replaced"] is True


def test_retrain_status_model_replaced_false_reflected_in_response():
    mock_db = MagicMock()
    mock_db.table.return_value.select.return_value.order.return_value \
        .limit.return_value.execute.return_value.data = [_RETRAIN_LOG_ROW_NOT_REPLACED]
    with patch("src.api.routes.supabase", mock_db):
        response = _client().get("/api/v1/monitor/retrain")
    assert response.json()["model_replaced"] is False


def test_retrain_status_returns_404_when_no_rows():
    mock_db = MagicMock()
    mock_db.table.return_value.select.return_value.order.return_value \
        .limit.return_value.execute.return_value.data = []
    with patch("src.api.routes.supabase", mock_db):
        response = _client().get("/api/v1/monitor/retrain")
    assert response.status_code == 404


def test_retrain_status_returns_500_on_supabase_error():
    mock_db = MagicMock()
    mock_db.table.return_value.select.return_value.order.return_value \
        .limit.return_value.execute.side_effect = Exception("supabase unreachable")
    with patch("src.api.routes.supabase", mock_db):
        response = _client().get("/api/v1/monitor/retrain")
    assert response.status_code == 500
```

Run pytest — all 5 must fail.

---

### Step 3 — implement route in `src/api/routes.py`

```python
@router.get("/monitor/retrain")
def get_retrain_status():
    try:
        result = (
            supabase.table("retrain_log")
            .select("timestamp,old_model_r2,new_model_r2,model_replaced,rows_used")
            .order("timestamp", desc=True)
            .limit(1)
            .execute()
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    if not result.data:
        raise HTTPException(status_code=404, detail="No retraining has run yet")
    return result.data[0]
```

Run pytest — all 5 must pass.

---

## Git

- **Branch:** `feat/015-retrain-status-endpoint`
- **Commit format:** `feat(api): add GET /api/v1/monitor/retrain — last retraining outcome`
- **PR title:** `feat(api): retrain status endpoint — returns most recent retrain_log row`
