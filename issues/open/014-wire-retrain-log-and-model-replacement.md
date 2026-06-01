---
id: "014"
slug: wire-retrain-log-and-model-replacement
feature: F3
epic: E5
title: Wire model replacement guard and retrain_log in run_retraining_if_ready
status: open
---

# 014 — Wire model replacement guard and `retrain_log` in `run_retraining_if_ready`

## Goal

Expose `run_retraining_if_ready` in `retrain_trigger.py` that checks the three
conditions, calls the retraining script if they are met, replaces the model file
only when the new R² exceeds the current one, writes the outcome to the Supabase
`retrain_log` table, and resets the drift flag and clean row counter — so the
model improves itself automatically and every decision is auditable.

## User Story

As a system operator, I want every automatic retraining attempt recorded in a
log table — including whether the model was replaced or kept — so I can audit
what the system decided and why.

## Reference Docs

- `CLAUDE.md` — Retraining Trigger conventions: model_full.meta.json sidecar, reset rules, retrain_log schema
- `docs/schema.md` — `retrain_log` table schema (add it here)
- `docs/api-contracts.md` — no new routes in this issue (routes in issue 015)
- `docs/decisions.md` — why old model is kept when new R² is lower

## Acceptance Criteria

- [ ] `retrain_log` schema added to `docs/schema.md` with fields: `id, timestamp, trigger_reason (text), old_model_r2 (float), new_model_r2 (float), model_replaced (bool), rows_used (int)`
- [ ] `test_run_retraining_if_ready_skips_when_should_retrain_false` — when `should_retrain` returns `False`, `run_retraining` is never called
- [ ] `test_run_retraining_if_ready_replaces_model_when_new_r2_higher` — when `run_retraining` returns `new_r2 > old_r2`, `model_full.joblib` is overwritten and `retrain_log` row has `model_replaced=True`
- [ ] `test_run_retraining_if_ready_keeps_model_when_new_r2_lower` — when `run_retraining` returns `new_r2 < old_r2`, model file is untouched and `retrain_log` row has `model_replaced=False`
- [ ] `test_run_retraining_if_ready_resets_drift_flag_after_retrain` — after a retrain attempt, drift flag is reset to `None` regardless of whether model was replaced
- [ ] `test_run_retraining_if_ready_inserts_retrain_log_row` — Supabase insert is called exactly once with a dict containing `model_replaced`, `old_model_r2`, `new_model_r2`, `rows_used`
- [ ] `test_scheduler_calls_run_retraining_if_ready_after_drift_check` — the scheduler's drift-check path calls `run_retraining_if_ready` at the end of every drift evaluation cycle
- [ ] All tests use mocked Supabase client, mocked joblib, mocked `run_retraining` — no real files or network

## Files to Modify

- `src/services/retrain_trigger.py` — add `run_retraining_if_ready`, drift-flag state
- `src/services/scheduler.py` — call `run_retraining_if_ready` at end of drift check
- `docs/schema.md` — add `retrain_log` table schema
- `tests/test_retrain_trigger.py` — add 6 tests above
- `tests/test_retrain_trigger.py` — add 1 scheduler integration test

## Out of Scope

- GET /api/v1/monitor/retrain endpoint (issue 015)
- Retraining model_simple.joblib or model_forecast.joblib
- Manual rollback of a replaced model

## Implementation Plan

### Step 1 — add `retrain_log` schema to `docs/schema.md`

Append under the existing Supabase tables section:

```
### retrain_log
| column          | type      | notes                                     |
|-----------------|-----------|-------------------------------------------|
| id              | uuid      | primary key, default gen_random_uuid()    |
| timestamp       | timestamptz | default now()                           |
| trigger_reason  | text      | human-readable summary of why triggered  |
| old_model_r2    | float8    | R² of model before retraining            |
| new_model_r2    | float8    | R² of best model from this run           |
| model_replaced  | boolean   | True if new file written                 |
| rows_used       | int4      | total rows (UCI + clean Supabase) used   |
```

---

### Step 2 — write all 7 failing tests

Add to `tests/test_retrain_trigger.py`:

```python
import json
import pytest
from unittest.mock import patch, MagicMock, call


_META_OLD = {"r2": 0.75}
_META_HIGHER = {"best_model": MagicMock(), "new_r2": 0.85, "rows_used": 2500}
_META_LOWER  = {"best_model": MagicMock(), "new_r2": 0.60, "rows_used": 2500}


def test_run_retraining_if_ready_skips_when_should_retrain_false():
    from src.services import retrain_trigger
    with patch.object(retrain_trigger, "should_retrain", return_value=False), \
         patch("scripts.run_retraining.run_retraining") as mock_run:
        retrain_trigger.run_retraining_if_ready(
            drift_detected=False, clean_row_count=100, total_row_count=110
        )
    mock_run.assert_not_called()


def test_run_retraining_if_ready_replaces_model_when_new_r2_higher():
    from src.services import retrain_trigger
    mock_supabase = MagicMock()
    with patch.object(retrain_trigger, "should_retrain", return_value=True), \
         patch("src.services.retrain_trigger.open",
               MagicMock(return_value=MagicMock(
                   __enter__=lambda s, *a: MagicMock(read=lambda: json.dumps(_META_OLD)),
                   __exit__=MagicMock(return_value=False)
               ))), \
         patch("scripts.run_retraining.run_retraining", return_value=_META_HIGHER), \
         patch("joblib.dump") as mock_dump, \
         patch("src.services.retrain_trigger.supabase", mock_supabase):
        retrain_trigger.run_retraining_if_ready(
            drift_detected=True, clean_row_count=2000, total_row_count=2200
        )
    mock_dump.assert_called_once()
    insert_call = mock_supabase.table("retrain_log").insert.call_args[0][0]
    assert insert_call["model_replaced"] is True


def test_run_retraining_if_ready_keeps_model_when_new_r2_lower():
    from src.services import retrain_trigger
    mock_supabase = MagicMock()
    with patch.object(retrain_trigger, "should_retrain", return_value=True), \
         patch("src.services.retrain_trigger._read_meta", return_value=_META_OLD), \
         patch("scripts.run_retraining.run_retraining", return_value=_META_LOWER), \
         patch("joblib.dump") as mock_dump, \
         patch("src.services.retrain_trigger.supabase", mock_supabase):
        retrain_trigger.run_retraining_if_ready(
            drift_detected=True, clean_row_count=2000, total_row_count=2200
        )
    mock_dump.assert_not_called()
    insert_call = mock_supabase.table("retrain_log").insert.call_args[0][0]
    assert insert_call["model_replaced"] is False


def test_run_retraining_if_ready_resets_drift_flag_after_retrain():
    from src.services import retrain_trigger
    retrain_trigger._drift_first_detected = "2026-05-01T00:00:00"
    with patch.object(retrain_trigger, "should_retrain", return_value=True), \
         patch("src.services.retrain_trigger._read_meta", return_value=_META_OLD), \
         patch("scripts.run_retraining.run_retraining", return_value=_META_HIGHER), \
         patch("joblib.dump"), \
         patch("src.services.retrain_trigger.supabase", MagicMock()):
        retrain_trigger.run_retraining_if_ready(
            drift_detected=True, clean_row_count=2000, total_row_count=2200
        )
    assert retrain_trigger._drift_first_detected is None


def test_run_retraining_if_ready_inserts_retrain_log_row():
    from src.services import retrain_trigger
    mock_supabase = MagicMock()
    with patch.object(retrain_trigger, "should_retrain", return_value=True), \
         patch("src.services.retrain_trigger._read_meta", return_value=_META_OLD), \
         patch("scripts.run_retraining.run_retraining", return_value=_META_HIGHER), \
         patch("joblib.dump"), \
         patch("src.services.retrain_trigger.supabase", mock_supabase):
        retrain_trigger.run_retraining_if_ready(
            drift_detected=True, clean_row_count=2000, total_row_count=2200
        )
    inserted = mock_supabase.table("retrain_log").insert.call_args[0][0]
    assert {"model_replaced", "old_model_r2", "new_model_r2", "rows_used"}.issubset(
        inserted.keys()
    )
    mock_supabase.table("retrain_log").insert.return_value.execute.assert_called_once()


def test_scheduler_calls_run_retraining_if_ready_after_drift_check():
    from src.services import scheduler
    with patch("src.services.scheduler.check_drift") as mock_drift, \
         patch("src.services.scheduler.run_retraining_if_ready") as mock_retrain, \
         patch("src.services.scheduler.fetch_row_counts", return_value=(2100, 2300)), \
         patch("src.services.scheduler.supabase", MagicMock()):
        mock_drift.return_value = True
        scheduler._drift_check_cycle()
    mock_retrain.assert_called_once()
```

Run pytest — all 6 tests must fail.

---

### Step 3 — implement `run_retraining_if_ready` in `retrain_trigger.py`

```python
import json
import os
import joblib
from datetime import datetime, timezone
from scripts.run_retraining import run_retraining
from src.services.database import supabase

_MODEL_PATH = os.environ.get("MODEL_PATH_FULL", "src/model/trained/model_full.joblib")
_META_PATH = _MODEL_PATH.replace(".joblib", ".meta.json")

_drift_first_detected: str | None = None


def _read_meta() -> dict:
    with open(_META_PATH) as f:
        return json.load(f)


def _write_meta(data: dict) -> None:
    with open(_META_PATH, "w") as f:
        json.dump(data, f)


def run_retraining_if_ready(
    drift_detected: bool,
    clean_row_count: int,
    total_row_count: int,
) -> None:
    global _drift_first_detected
    if not should_retrain(drift_detected, clean_row_count, total_row_count):
        return

    old_meta = _read_meta()
    old_r2 = old_meta.get("r2", 0.0)

    result = run_retraining()
    new_r2 = result["new_r2"]
    model_replaced = new_r2 > old_r2

    if model_replaced:
        joblib.dump(result["best_model"], _MODEL_PATH)
        _write_meta({"r2": new_r2})

    supabase.table("retrain_log").insert({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "trigger_reason": "drift + row_count + anomaly_rate all met",
        "old_model_r2": old_r2,
        "new_model_r2": new_r2,
        "model_replaced": model_replaced,
        "rows_used": result["rows_used"],
    }).execute()

    _drift_first_detected = None
```

---

### Step 4 — wire into `scheduler.py`

At the end of the drift-check function in `scheduler.py`, add:

```python
from src.services.retrain_trigger import run_retraining_if_ready

# inside _drift_check_cycle(), after check_drift() returns:
clean_count, total_count = fetch_row_counts()
run_retraining_if_ready(
    drift_detected=drift_flagged,
    clean_row_count=clean_count,
    total_row_count=total_count,
)
```

Run pytest — all 7 tests must pass.

---

## Git

- **Branch:** `feat/014-retrain-log-and-model-replacement`
- **Commit format:** `feat(retrain): add run_retraining_if_ready with model guard and retrain_log`
- **PR title:** `feat(retrain): wire model replacement guard, retrain_log, and scheduler integration`
