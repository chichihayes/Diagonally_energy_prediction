---
epic: E5-monitoring-and-retraining
feature: F2
slug: drift-detection
---

# F2 — Rolling Mean Drift Detection with Drift Log

## Goal

Every 100 clean (non-anomalous) readings, the system checks whether the
real-world data distribution has drifted from the training distribution by
computing the rolling mean deviation for all 25 features. Any feature with
more than 15% deviation from its training mean triggers a drift flag. The
event is logged to the Supabase `drift_log` table and exposed through a
`GET /api/v1/monitor/drift` endpoint so a system operator can query current
drift status at any time.

## User Story

As a system operator, I want to know when real house data consistently differs
from the training data so I can audit drift events and understand when
retraining conditions are approaching.

## Issues

1. **Implement drift detection in retrain_trigger.py** — Expose
   `check_drift(clean_readings: list[dict]) -> dict` that accepts the last 100
   clean feature dicts, computes the rolling mean for each of the 25 features,
   loads training means from `training_stats.json`, and returns
   `{"drift_detected": bool, "drifted_features": list,
   "deviations": {"feature": float}}` where deviation is
   `abs(rolling_mean - training_mean) / training_mean * 100`. Any feature
   deviation above 15% sets `drift_detected=True`. Raise `ValueError` if fewer
   than 100 readings are passed.

2. **Create Supabase drift_log table and store drift events** — Add `drift_log`
   table schema to `docs/schema.md`:
   `id, timestamp, drifted_features (text[]),
   deviations (JSONB), clean_row_count (int)`.
   In `database.py`, add `store_drift_event(record: dict)` that inserts one row
   per drift check (regardless of whether drift was detected) so the operator
   has a complete audit trail. Call `store_drift_event` from the scheduler tick
   whenever the clean reading count crosses a multiple of 100.

3. **Wire drift check into the scheduler** — In `scheduler.py`, maintain a
   module-level counter of clean readings since the last drift check. After
   every successful prediction tick where `low_confidence=False`, increment the
   counter. When the counter reaches 100, fetch the last 100 clean feature dicts
   from Supabase, call `check_drift`, call `store_drift_event`, then reset the
   counter to 0. If the Supabase fetch fails, log the error and skip — do not
   crash the scheduler.

4. **Add GET /api/v1/monitor/drift endpoint** — Return the most recent row from
   `drift_log` as `{"timestamp": str, "drift_detected": bool,
   "drifted_features": list, "deviations": dict, "clean_row_count": int}`.
   Return 404 if no drift check has been run yet. Write tests in
   `test_retrain_trigger.py`: 100 readings with one feature 20% above training
   mean returns `drift_detected=True`; 100 normal readings return
   `drift_detected=False`; fewer than 100 readings raises `ValueError`.

## Out of Scope

- PSI or KS-Test drift methods
- Per-feature drift threshold configuration (15% is fixed)
- Automatic retraining triggered by drift alone (requires F3's 3-condition
  check)
- Drift visualisation on the frontend
