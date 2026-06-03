# CLAUDE.md — Diagonally Energy Prediction

## What this app is
Diagonally Energy Prediction is a machine learning system that predicts household
appliance energy consumption for a UK home using the REFIT Smart Home Dataset (House 1).
It covers 9 individual appliances (Fridge, ChestFreezer, UprightFreezer, TumbleDryer,
WashingMachine, Dishwasher, Computer, Television, ElectricHeater) over the period
October 9 – January 2 2014.

The system trains a time series forecast model (Chronos-Bolt, MSTL, or XGBoost with
lags) to predict future consumption over 24 hours and 7 days.

A scheduler replays the test split (Dec 16 – Jan 2 2014) rows every 15 minutes,
storing per-appliance and actual-aggregate values in Supabase. A lightweight
HTML + JavaScript frontend shows predicted consumption and estimated electricity
cost in GBP (£). Drift detection and automatic retraining are built in.

## Stack
- Language: Python 3.11
- API: FastAPI + Uvicorn
- Time Series Models: Chronos-Bolt (Small), MSTL, XGBoost with lag features — all trained and evaluated, best MAPE saved as final model
- Data: pandas, numpy, scikit-learn
- Model persistence: joblib
- Dataset: REFIT Smart Home Dataset — House 1 (data/raw/House1.csv, Oct 2013 – Jan 2014, 8-second intervals)
- Frontend: HTML + JavaScript (no framework, no build step) + Tailwind CSS via CDN
- Database: Supabase (Postgres) — stores per-appliance predictions, forecasts, drift logs
- Scheduler: APScheduler — replays test split rows every 15 minutes
- Cost calculation: Ofgem UK tariff rate (GBP) applied to predicted kWh
- Testing: pytest + httpx
- CI: GitHub Actions

## Environment variables
```
MODEL_PATH_FORECAST=src/model/trained/model_forecast.joblib
TEST_SPLIT_PATH=data/processed/test.csv
API_HOST=0.0.0.0
API_PORT=8000
SUPABASE_URL=
SUPABASE_ANON_KEY=
SUPABASE_SERVICE_ROLE_KEY=
ELECTRICITY_TARIFF_GBP_PER_KWH=0.34
```

## Spec documents (read before touching any file)
- `docs/schema.md` — data schema, feature definitions, input/output shapes
- `docs/api-contracts.md` — every route, request shape, response shape
- `docs/architecture.md` — file structure, data flow, service boundaries
- `docs/decisions.md` — why things are built the way they are
- `docs/env.md` — environment variables reference

## Module map
```
diagonally-energy-prediction/
├── data/
│   ├── raw/                              # original REFIT dataset (House1.csv)
│   └── processed/                        # cleaned and engineered features + lag features
├── notebooks/                            # EDA, model comparison, feature importance
├── frontend/
│   ├── dashboard.html                    # Smart Home tier live dashboard
│   ├── forecast.html                     # 7-day forecast and weekly bill projection
│   └── assets/
│       ├── style.css                     # custom styles
│       └── app.js                        # API calls and UI logic
├── src/
│   ├── api/
│   │   ├── main.py                       # FastAPI app entry point + APScheduler startup
│   │   └── routes.py                     # all prediction and forecast endpoints
│   ├── model/
│   │   ├── train_forecast.py             # train all 3 time series models — save best MAPE
│   │   ├── evaluate.py                   # write_leaderboard helper
│   │   ├── forecast.py                   # load forecast model singleton and return predictions
│   │   └── trained/
│   │       ├── model_forecast.joblib     # best time series model (gitignored)
│   │       ├── forecast_leaderboard.json # MAPE/MAE/RMSE for all 3 trained models
│   │       └── training_stats.json       # per-feature mean + std from train split
│   └── services/
│       ├── features.py                   # build_lag_matrix for forecast training
│       ├── data_loader.py                # load and preprocess House1.csv
│       ├── cost.py                       # Wh to GBP conversion + weekly bill projection
│       ├── database.py                   # Supabase insert and retrieve predictions and forecasts
│       ├── scheduler.py                  # APScheduler — replay test rows every 15 minutes
│       ├── monitor.py                    # Z-Score anomaly detection on every incoming reading
│       └── retrain_trigger.py            # checks 3 conditions every 100 readings: drift > 15%, clean rows > 2000, anomaly rate < 10%
├── tests/
│   ├── test_api.py                       # endpoint tests for all routes
│   ├── test_features.py                  # lag feature tests
│   ├── test_model.py                     # data loader and forecast model tests
│   ├── test_forecast.py                  # time series forecast tests
│   ├── test_evaluate.py                  # leaderboard tests
│   ├── test_cost.py                      # cost calculation and bill projection tests
│   ├── test_database.py                  # Supabase storage tests
│   ├── test_monitor.py                   # Z-Score anomaly detection tests
│   └── test_retrain_trigger.py           # retraining condition tests
├── scripts/
│   ├── run_training_forecast.py          # train all time series models, save best forecast model
│   └── run_retraining.py                 # retraining trigger — fetches clean rows, retrains forecast model
└── .github/workflows/
    └── ci.yml                            # run all tests on push to main
```

## ML conventions

Time Series Forecast:
- Three models trained and evaluated: Chronos-Bolt (Small), MSTL, XGBoost with lag features
- Evaluation metrics: MAE, RMSE, MAPE on held-out test split
- Best MAPE model saved as model_forecast.joblib
- Leaderboard saved as src/model/trained/forecast_leaderboard.json
- All models trained on aggregate_wh time series from train split
- Forecast horizons: 24 hours ahead (hourly) and 7 days ahead (daily)
- All forecast models return: yhat, yhat_lower, yhat_upper (confidence interval)
- Never expose raw model output to the API — always format into clean JSON
- forecast.py loads best model once at startup as a singleton
- Retrain by running scripts/run_training_forecast.py — never retrain inside the API

Layer 2 — Bill Estimation (No Model):
- Pure calculation — no ML model involved
- Formula: projected_week_bill = sum(7-day forecast_kwh) × ELECTRICITY_TARIFF_GBP_PER_KWH
- No extrapolation — 7-day forecast covers exactly 7 days; result is the actual 7-day cost in GBP
- Return optimistic (lower_wh), pessimistic (upper_wh) and most likely (predicted_wh) weekly bill projections
- Always read tariff from ELECTRICITY_TARIFF_GBP_PER_KWH environment variable
- Round all GBP values to 2 decimal places
- Response key: projected_week_bill with fields: optimistic_gbp, most_likely_gbp, pessimistic_gbp, period ("7 days")

## Monitoring and retraining conventions

Anomaly Detection — Z-Score (every 15 min reading):
- Formula: Z = (new_value - training_mean) / training_std
- Training mean and std calculated once from train split and saved in src/model/trained/training_stats.json
- Check all 13 MODEL_FEATURES on every incoming reading
- Z > 3 on ANY feature → reading flagged as anomaly
- Anomalous readings stored in Supabase anomalies table with anomaly=True
- Prediction still made but marked low_confidence=True
- Anomalous readings NOT counted toward clean row pool
- Never use anomalous readings for retraining

Drift Detection — Rolling Mean Deviation (every 100 clean readings):
- Formula: deviation = |rolling_mean - training_mean| / training_mean × 100
- training_mean is fixed from train split — never changes
- rolling_mean is mean of last 100 clean readings for each feature
- Check all 13 MODEL_FEATURES
- Any feature deviation > 15% → drift flagged
- Drift flagged → log to Supabase drift_log table
- Drift flagged → start counting toward retraining threshold

Retraining Trigger — 3 conditions must ALL be true:
- Condition 1: Drift detected (at least one feature deviation > 15%)
- Condition 2: At least 2000 clean rows accumulated in Supabase since drift was first flagged
- Condition 3: Anomaly rate < 10% (clean rows / total rows > 90%)
- When all 3 met: pull all clean rows from Supabase, retrain all 3 forecast models, evaluate on held-out set, save best MAPE model
- If new model MAPE < old model MAPE → replace model_forecast.joblib
- If new model MAPE >= old model MAPE → keep old model
- Log outcome to Supabase retrain_log table either way
- Reset clean row counter and drift flag after retraining

Supabase tables for monitoring:
- anomalies: id, timestamp, features (JSONB — MODEL_FEATURES dict), z_scores (JSONB), flagged_features (text[])
- drift_log: id, timestamp, drift_detected (bool), drifted_features (text[]), deviations (JSONB — feature→pct), clean_row_count (int)
- retrain_log: id, timestamp, trigger_reason, old_mape, new_mape, model_replaced (bool), rows_used

## Database conventions
- Always use supabase-py client — never raw psycopg2
- DB reads: supabase.table('predictions').select('*').execute()
- DB writes: supabase.table('predictions').insert({}).execute()
- RLS enabled on all tables — every request must pass the correct key
- predictions table stores: id, created_at, tier, input_features (JSON),
  predicted_wh, predicted_kwh, estimated_cost_gbp, aggregate_wh,
  fridge_wh, chest_freezer_wh, upright_freezer_wh, tumble_dryer_wh,
  washing_machine_wh, dishwasher_wh, computer_wh, television_wh,
  electric_heater_wh, low_confidence (bool), anomaly (bool)
- Never store raw model files or training data in Supabase

## Cost calculation conventions
- Always convert Wh to kWh before applying tariff: predicted_kwh = predicted_wh / 1000
- Tariff rate comes from environment variable ELECTRICITY_TARIFF_GBP_PER_KWH
- Never hardcode the tariff rate inside any function — always read from env
- Formula: estimated_cost_gbp = predicted_kwh * ELECTRICITY_TARIFF_GBP_PER_KWH
- Round cost to 2 decimal places before returning in API response

## Scheduler conventions
- APScheduler runs as a background service inside the FastAPI app
- Interval: every 15 minutes
- On each tick: get next row from test.csv (Dec 16 – Jan 2) → use actual aggregate_wh as predicted_wh → store result + per-appliance actuals in Supabase
- If Supabase write fails: log the error, skip the tick, do not crash
- Scheduler replays test split rows chronologically (cycling); no sensor env vars needed
- No model inference on the scheduler tick — predicted_wh comes directly from aggregate_wh column

## Frontend conventions
- Pure HTML + JavaScript — no React, no Vue, no build step
- Tailwind CSS via CDN for styling
- dashboard.html — Smart Home tier: live per-appliance breakdown + 24h history chart, auto-refreshes every 15 minutes
- forecast.html — 24h/7d forecast charts + weekly bill projection (GBP) + model leaderboard
- app.js makes fetch() calls to the FastAPI API — no direct Supabase calls from frontend
- All API responses display: predicted Wh, predicted kWh, estimated cost in GBP (£)
- Frontend must be responsive — works on mobile and desktop
- No authentication for the demo — API is open

## Naming conventions
- Files: snake_case
- Functions: snake_case
- Routes: /kebab-case
- Feature columns: snake_case

## Error handling
- Raise HTTPException with correct status code — nothing else
- 400 bad input, 422 validation error, 500 model error
- Never catch exceptions silently
- Never return 200 with an error in the body

## TDD rules
- Write the failing test first. Confirm it fails. Then implement.
- Every function that transforms data or calls the model has a test
- A test that passes before implementation exists is wrong — fix the test

## Coding standards
- Minimum code that solves the problem. Nothing speculative.
- No features beyond what was asked
- No abstractions for single-use code
- If it could be 50 lines, do not write 200
- Every changed line traces directly to the task
- Do not touch files outside the task scope
- Match existing style even if you would do it differently

## Communication style
- State assumptions before implementing
- If multiple interpretations exist, present them — do not pick silently
- If something is unclear, stop and ask
- Surface tradeoffs before choosing an approach
