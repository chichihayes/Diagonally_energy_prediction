---
epic: E5-monitoring-and-retraining
feature: F3
slug: retraining-trigger
---

# F3 — Automatic Retraining Trigger with Outcome Log

## Goal

When all three conditions are simultaneously true — drift detected, at least
2000 clean rows accumulated since drift was first flagged, and anomaly rate
below 10% — the system automatically retrains all six regression models on the
combined UCI dataset plus clean Supabase rows. If the new best R² exceeds the
current model's R², the model file is replaced. The outcome is written to the
Supabase `retrain_log` table whether or not the model was replaced. A system
operator can query `GET /api/v1/monitor/retrain` to see the most recent
retraining outcome.

## User Story

As a system operator, I want the model to automatically improve when real house
data consistently differs from the training data so predictions stay accurate
over time without manual intervention.

## Issues

1. **Implement 3-condition check in retrain_trigger.py** — Expose
   `should_retrain(drift_detected: bool, clean_row_count: int,
   total_row_count: int) -> bool` that returns `True` only when all three
   conditions hold: `drift_detected is True`, `clean_row_count >= 2000`, and
   `clean_row_count / total_row_count >= 0.90`. Store the drift-first-detected
   timestamp as a module-level variable, reset it to `None` after a retraining
   run. Write unit tests in `test_retrain_trigger.py` covering all 8 combinations
   of the 3 boolean conditions, confirming only the all-true case returns `True`.

2. **Implement scripts/run_retraining.py** — Fetch all clean rows from the
   Supabase `predictions` table (where `low_confidence=False`). Combine with the
   UCI CSV (`data/raw/KAG_energydata_complete.csv`). Drop `rv1`, `rv2`. Train
   all six regression models on the combined dataset (80/20 time-ordered split).
   Evaluate R² on the held-out split. Return `{"best_model": model,
   "new_r2": float, "rows_used": int}`. Do not write any model files — that is
   the caller's responsibility.

3. **Create Supabase retrain_log table and wire model replacement guard** —
   Add `retrain_log` schema to `docs/schema.md`:
   `id, timestamp, trigger_reason (text), old_model_r2 (float),
   new_model_r2 (float), model_replaced (bool), rows_used (int)`.
   In `retrain_trigger.py`, expose `run_retraining_if_ready(...)` that calls
   `should_retrain`, and if true: reads the current model's R² from a metadata
   sidecar file (`model_full.meta.json`), calls `run_retraining.py`, writes the
   new model to `model_full.joblib` only if `new_r2 > old_r2`, updates
   `model_full.meta.json`, inserts a row into `retrain_log`, then resets the
   drift flag and clean row counter. Call `run_retraining_if_ready` from
   `scheduler.py` at the end of every drift check.

4. **Add GET /api/v1/monitor/retrain endpoint** — Return the most recent row
   from `retrain_log` as `{"timestamp": str, "old_model_r2": float,
   "new_model_r2": float, "model_replaced": bool, "rows_used": int}`. Return
   404 if retraining has never run. Write tests in `test_retrain_trigger.py`:
   mock `run_retraining.py` to return a higher R² and confirm model file is
   replaced and `retrain_log` row has `model_replaced=True`; mock a lower R²
   and confirm model file is unchanged and `model_replaced=False`.

## Out of Scope

- Retraining model_simple.joblib or model_forecast.joblib (full tier only)
- Manual review gate before model replacement
- Rollback mechanism after a bad model swap
- Per-appliance retraining
- Retraining triggered by anomaly rate alone without drift
