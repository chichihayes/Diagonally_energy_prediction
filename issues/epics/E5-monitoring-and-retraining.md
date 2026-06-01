# Epic E5 — Monitoring and Retraining

## Goal
Ensure the prediction system remains accurate 
over time by detecting anomalous sensor readings 
in real time and automatically retraining models 
when the incoming data distribution drifts 
significantly from the training data.

## User Stories
- As a homeowner, I want predictions to be marked 
  low confidence when sensor readings look unusual 
  so I know when to check my sensors.
- As a system operator, I want the model to 
  automatically improve when real house data 
  consistently differs from the training data 
  so predictions stay accurate over time.
- As a system operator, I want all anomalies, 
  drift events and retraining outcomes logged 
  so I can audit the system manually.

## Features
- F1: Z-Score anomaly detection on every 
      15-minute reading
- F2: Rolling mean drift detection every 
      100 clean readings
- F3: Automatic retraining trigger when 
      all 3 conditions met
- F4: Monitoring logs in Supabase 
      (anomalies, drift_log, retrain_log)

## Technical Details

### Anomaly Detection (F1)
- Technique: Z-Score
- Formula: Z = (new_value - training_mean) / training_std
- Threshold: Z > 3 on any feature → anomaly
- Reference: training_stats.json 
  (saved once at training time)
- Action: flag reading, mark prediction 
  low_confidence=True, store in anomalies table

### Drift Detection (F2)
- Technique: Rolling Mean Percentage Deviation
- Formula: abs(rolling_mean - training_mean) 
  / training_mean × 100
- Window: last 100 clean readings
- Threshold: any feature > 15% → drift flagged
- Action: log to drift_log, start counting 
  toward retraining threshold

### Retraining Trigger (F3)
- Condition 1: Drift detected
- Condition 2: 2000+ clean rows accumulated
- Condition 3: Anomaly rate < 10%
- Action: retrain all 6 models on UCI + 
  Supabase clean rows, save best R², 
  log to retrain_log
- Guard: only replace model if new R² > old R²

### New Supabase Tables (F4)
- anomalies: stores every flagged reading
- drift_log: stores every drift detection result
- retrain_log: stores every retraining outcome

## Out of Scope
- PSI or KS-Test drift detection 
  (future enhancement)
- Per-appliance anomaly detection
- Real-time alerts or notifications on anomaly
- Automatic sensor recalibration

## Dependencies
- Blocked by: model training complete 
  (training_stats.json must exist)
- Blocked by: Supabase schema set up
