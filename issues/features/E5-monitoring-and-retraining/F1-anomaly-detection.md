---
epic: E5-monitoring-and-retraining
feature: F1
slug: anomaly-detection
---

# F1 — Z-Score Anomaly Detection with Low Confidence Flag

## Goal

Every incoming prediction request is checked against the training distribution
before the model runs. If any of the 25 input features has a Z-Score above 3
standard deviations from the training mean, the reading is flagged as an
anomaly, the prediction is marked `low_confidence: true` in the API response,
and the flagged reading is stored in the Supabase `anomalies` table. The
homeowner sees the low confidence flag immediately so they know to check their
sensors.

## User Story

As a homeowner, I want predictions to be marked low confidence when sensor
readings look unusual so I know when to check my sensors.

## Issues

1. **Save training_stats.json from UCI dataset** — In
   `scripts/run_training_full.py`, after loading the preprocessed dataset,
   compute the mean and standard deviation for all 25 input features from the
   training split (first 80% of rows, time-ordered). Save the result to
   `src/model/trained/training_stats.json` as `{"feature": {"mean": float,
   "std": float}}`. This file is the fixed reference for all future Z-Score
   checks — never overwrite it during retraining.

2. **Implement monitor.py** — Load `training_stats.json` once at module import
   as a singleton. Expose `check_anomaly(features: dict) -> dict` that computes
   `Z = (value - mean) / std` for each feature, returns
   `{"is_anomaly": bool, "z_scores": dict, "flagged_features": list}`.
   Any feature with `abs(Z) > 3` sets `is_anomaly=True`. If std is zero for a
   feature, skip that feature's check.

3. **Create Supabase anomalies table and store flagged readings** — Add the
   `anomalies` table schema to `docs/schema.md`:
   `id, timestamp, tier, input_features (JSONB), z_scores (JSONB),
   flagged_features (text[]), low_confidence_prediction (bool)`.
   In `database.py`, add `store_anomaly(record: dict)` that inserts into the
   `anomalies` table. Call `store_anomaly` from the prediction route whenever
   `is_anomaly=True`. Anomalous readings are stored but never counted as clean
   rows.

4. **Add low_confidence field to prediction API responses** — In `routes.py`,
   call `check_anomaly` on every incoming feature dict before running inference
   (both `/predict/simple` and `/predict/full`). Append `"low_confidence":
   true` to the response JSON when `is_anomaly=True`; `"low_confidence": false`
   otherwise. Write tests in `test_monitor.py`: a feature dict with one value
   30 std devs from mean returns `is_anomaly=True`; a normal dict returns
   `is_anomaly=False`. Write tests in `test_api.py`: response body always
   contains the `low_confidence` field.

## Out of Scope

- Real-time push alerts or email notifications when an anomaly is detected
- Per-appliance anomaly detection
- UI indicator for low confidence on the frontend
- Drift detection or retraining logic (covered in F2 and F3)
