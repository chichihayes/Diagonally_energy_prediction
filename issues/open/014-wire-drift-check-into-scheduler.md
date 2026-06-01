---
epic: E5-monitoring-and-retraining
feature: F2
slug: wire-drift-check-into-scheduler
---

# 014 — Wire Drift Check into Scheduler Counter

## Goal

As a system operator, I want the scheduler to automatically check for data drift every 100 clean readings so drift detection runs continuously without manual intervention.

## User Story

As a system operator, I want the 15-minute scheduler tick to maintain a running count of clean (non-anomalous) readings, and when that count reaches 100, automatically run the drift check, persist the result, and reset the counter.

## Reference Docs

- `docs/architecture.md` — scheduler responsibilities and tick lifecycle
- `docs/decisions.md` — why drift is checked every 100 readings, not every tick

## Acceptance Criteria

- [ ] `scheduler.py` has a module-level integer `_clean_reading_count` initialised to `0`
- [ ] On each tick that produces a `low_confidence=False` prediction, `_clean_reading_count` increments by 1
- [ ] On each tick that produces a `low_confidence=True` prediction (anomaly), `_clean_reading_count` is NOT incremented
- [ ] When `_clean_reading_count` reaches 100: fetch the last 100 clean feature dicts from Supabase, call `check_drift`, call `store_drift_event` with the result, then reset `_clean_reading_count` to `0`
- [ ] If the Supabase fetch raises an exception: log the error, reset `_clean_reading_count` to `0`, and do not crash the scheduler
- [ ] `check_drift` and `store_drift_event` are never called when `_clean_reading_count < 100`

## Files to Modify

- `src/services/scheduler.py` — add `_clean_reading_count` and drift check trigger
- `tests/test_scheduler.py` — add tests (write first, confirm they fail, then implement)

## Out of Scope

- The `check_drift` implementation itself (Issue 012)
- The `store_drift_event` / `get_latest_drift_event` functions (Issue 013)
- Retraining trigger logic (F3)

## Implementation Plan

### Step 1 — Write failing tests in `tests/test_scheduler.py`

**Test:** `test_scheduler_increments_clean_reading_count_on_non_anomalous_tick`
- Reset `scheduler._clean_reading_count = 0`
- Mock `predict_full` to return a result with `low_confidence=False`
- Mock Supabase write to succeed
- Call the scheduler tick function once
- Assert: `scheduler._clean_reading_count == 1`

**Test:** `test_scheduler_does_not_increment_count_on_anomalous_tick`
- Reset `scheduler._clean_reading_count = 0`
- Mock `predict_full` to return a result with `low_confidence=True`
- Call the scheduler tick function once
- Assert: `scheduler._clean_reading_count == 0`

**Test:** `test_scheduler_triggers_drift_check_at_100_and_resets_counter`
- Set `scheduler._clean_reading_count = 99`
- Mock Supabase fetch of last 100 clean readings to return a list of 100 feature dicts
- Mock `check_drift` to return `{"drift_detected": False, "drifted_features": [], "deviations": {}}`
- Mock `store_drift_event` to do nothing
- Mock `predict_full` returning `low_confidence=False`
- Call tick once
- Assert: `check_drift` was called once with a list of length 100
- Assert: `store_drift_event` was called once
- Assert: `scheduler._clean_reading_count == 0`

**Test:** `test_scheduler_does_not_trigger_drift_check_below_100`
- Set `scheduler._clean_reading_count = 50`
- Mock `predict_full` returning `low_confidence=False`
- Call tick once
- Assert: `check_drift` was NOT called
- Assert: `store_drift_event` was NOT called
- Assert: `scheduler._clean_reading_count == 51`

**Test:** `test_scheduler_resets_counter_and_skips_drift_check_on_fetch_failure`
- Set `scheduler._clean_reading_count = 99`
- Mock Supabase clean readings fetch to raise `Exception("connection timeout")`
- Mock `predict_full` returning `low_confidence=False`
- Call tick once
- Assert: `check_drift` was NOT called
- Assert: `store_drift_event` was NOT called
- Assert: `scheduler._clean_reading_count == 0`

### Step 2 — Implement in `src/services/scheduler.py`

1. Add at module level:
   ```python
   _clean_reading_count: int = 0
   ```

2. In the tick function, after storing the prediction result:
   ```python
   global _clean_reading_count
   if not low_confidence:
       _clean_reading_count += 1
   if _clean_reading_count >= 100:
       try:
           clean_rows = database.get_last_n_clean_readings(100)
           drift_result = check_drift(clean_rows)
           store_drift_event({**drift_result, "clean_row_count": 100, "timestamp": datetime.utcnow().isoformat()})
       except Exception as e:
           logger.error(f"Drift check failed: {e}")
       finally:
           _clean_reading_count = 0
   ```

   Note: `database.get_last_n_clean_readings(n)` fetches `n` rows from the `predictions` table where `low_confidence=False`, ordered by `created_at desc`, returning just the `inputs` JSONB column as a list of dicts.

### Step 3 — Confirm all 5 tests pass

Run `pytest tests/test_scheduler.py -v -k drift` and verify green.

## Git

- Branch: `feat/E5-F2-scheduler-drift-counter`
- Commit: `feat(scheduler): add clean reading counter and drift check trigger every 100 readings`
- PR: `feat: Wire drift detection into scheduler — trigger every 100 clean readings`
