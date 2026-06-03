# CLAUDE.md â€” Diagonally Energy Prediction

## What this app is
Diagonally Energy Prediction is a machine learning system that predicts household
appliance energy consumption for a UK home using the REFIT Smart Home Dataset (House 1).
It covers 9 individual appliances (Fridge, ChestFreezer, UprightFreezer, TumbleDryer,
WashingMachine, Dishwasher, Computer, Television, ElectricHeater) over the period
October 9 – January 2 2014.

The system trains a regression model to predict aggregate energy consumption from
time-based and lag features, and a time series forecast model (Chronos-Bolt, MSTL,
or XGBoost with lags) to predict future consumption over 24 hours and 7 days.

A scheduler replays the test split (Dec 16 – Jan 2 2014) rows every 15 minutes,
storing per-appliance and predicted-aggregate values in Supabase. A lightweight
HTML + JavaScript frontend shows predicted consumption and estimated electricity
cost in GBP (£). Drift detection and automatic retraining are built in.

## Stack
- Language: Python 3.11
- API: FastAPI + Uvicorn
- Regression Models (Layer 1): Random Forest, XGBoost, LightGBM, CatBoost, Extra Trees, Ridge Regression — all trained and evaluated, best R² saved as final model
- Time Series Models (Layer 2): Chronos-Bolt (Small), MSTL, XGBoost with lag features — all trained and evaluated, best MAPE saved as final model
- Data: pandas, numpy, scikit-learn (StandardScaler)
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
MODEL_PATH_FULL=src/model/trained/model_full.joblib
MODEL_PATH_FORECAST=src/model/trained/model_forecast.joblib
SCALER_PATH=src/model/trained/scaler.joblib
TEST_SPLIT_PATH=data/processed/test.csv
API_HOST=0.0.0.0
API_PORT=8000
SUPABASE_URL=
SUPABASE_ANON_KEY=
SUPABASE_SERVICE_ROLE_KEY=
ELECTRICITY_TARIFF_GBP_PER_KWH=0.34
```

## Spec documents (read before touching any file)
- `docs/schema.md` â€” data schema, feature definitions, input/output shapes
- `docs/api-contracts.md` â€” every route, request shape, response shape
- `docs/architecture.md` â€” file structure, data flow, service boundaries
- `docs/decisions.md` â€” why things are built the way they are
- `docs/env.md` â€” environment variables reference

## Module map
```
diagonally-energy-prediction/
├── data/
│   ├── raw/                              # original UCI dataset (KAG_energydata_complete.csv)
│   └── processed/                        # cleaned and engineered features + lag features
├── notebooks/                            # EDA, model comparison, feature importance
├── frontend/
│   ├── index.html                        # landing page with tier selection
│   ├── simple.html                       # Basic tier form and results
│   ├── dashboard.html                    # Smart Home tier live dashboard
│   ├── forecast.html                     # 7-day forecast and monthly bill projection
│   └── assets/
│       ├── style.css                     # custom styles
│       └── app.js                        # API calls and UI logic
├── src/
│   ├── api/
│   │   ├── main.py                       # FastAPI app entry point + APScheduler startup
│   │   └── routes.py                     # all prediction and forecast endpoints
│   ├── model/
│   │   ├── train_full.py                 # train all 6 regression models on 25 features — save best R²
│   │   ├── train_simple.py               # train all 6 regression models on 7 features — save best R²
│   │   ├── train_forecast.py             # train all 5 time series models — save best MAPE
│   │   ├── evaluate.py                   # compare all models, print leaderboard, return best
│   │   ├── predict.py                    # load regression model singletons and run inference
│   │   ├── forecast.py                   # load forecast model singleton and return predictions
│   │   └── trained/
│   │       ├── model_full.joblib         # best regression model on 25 features
│   │       ├── model_simple.joblib       # best regression model on 7 features
│   │       └── model_forecast.joblib     # best time series model
│   └── services/
│       ├── features.py                   # assemble feature dicts for both tiers + lag features
│       ├── data_loader.py                # load and preprocess KAG_energydata_complete.csv
│       ├── cost.py                       # Wh to NGN conversion + monthly bill projection
│       ├── database.py                   # Supabase insert and retrieve predictions and forecasts
│       ├── scheduler.py                  # APScheduler — auto-submit readings every 15 minutes
│       ├── monitor.py                    # Z-Score anomaly detection on every incoming reading — flags if any feature Z > 3 std devs from training mean
│       └── retrain_trigger.py            # checks 3 conditions every 100 readings: drift > 15%, clean rows > 2000, anomaly rate < 10% — triggers retraining when all 3 met
├── tests/
│   ├── test_api.py                       # endpoint tests for all routes
│   ├── test_features.py                  # feature assembly and lag feature tests
│   ├── test_model.py                     # regression model inference tests
│   ├── test_forecast.py                  # time series forecast tests
│   ├── test_evaluate.py                  # model comparison and leaderboard tests
│   ├── test_cost.py                      # cost calculation and bill projection tests
│   ├── test_database.py                  # Supabase storage tests
│   ├── test_monitor.py                   # Z-Score anomaly detection tests
│   └── test_retrain_trigger.py           # retraining condition tests
├── scripts/
│   ├── run_training_full.py              # train all regression models, save best for full tier
│   ├── run_training_simple.py            # train all regression models, save best for simple tier
│   ├── run_training_forecast.py          # train all time series models, save best forecast model
│   └── run_retraining.py                 # manual retraining trigger — pulls clean rows from Supabase + UCI dataset, retrains all 6 models, saves best R²
└── .github/workflows/
    └── ci.yml                            # run all tests on push to main
```

## ML conventions

Layer 1 — Current Consumption (Regression):
- Six models trained and evaluated: Random Forest, XGBoost, LightGBM, CatBoost, Extra Trees, Ridge Regression
- All six trained on MODEL_FEATURES (13 features) against aggregate_wh target
- Train split: Oct 9 – Dec 15 2013. Test split: Dec 16 2013 – Jan 2 2014. Never shuffle.
- Evaluation metric: R² score on held-out test split
- Best R² model saved as model_full.joblib
- MODEL_FEATURES: hour, day_of_week, month, is_weekend, is_night, is_peak_hour, lag_1, lag_6, lag_144, lag_1008, rolling_mean_6, rolling_mean_144, rolling_std_6
- is_night = 1 if hour >= 22 or hour < 6 (UK hours)
- is_peak_hour = 1 if 16 <= hour <= 20 (UK peak demand)
- All MODEL_FEATURES StandardScaler-transformed; scaler saved as scaler.joblib
- Never pull all rows into memory for prediction — accept feature dict, return float
- All models loaded once at startup as global singletons — never reload per request
- Retrain by running scripts/run_training_full.py — never retrain inside the API

Layer 2 — Future Consumption (Time Series):
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

Layer 3 — Bill Estimation (No Model):
- Pure calculation — no ML model involved
- Formula: projected_bill_gbp = sum(forecast_kwh) × ELECTRICITY_TARIFF_GBP_PER_KWH
- Return optimistic (yhat_lower), pessimistic (yhat_upper) and most likely (yhat) bill projections
- Always read tariff from ELECTRICITY_TARIFF_GBP_PER_KWH environment variable
- Round all GBP values to 2 decimal places

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
- When all 3 met: pull all clean rows from Supabase, combine with train split data, retrain all 6 models, evaluate on held-out set, save best R² model
- If new model R² > old model R² → replace model
- If new model R² < old model R² → keep old model
- Log outcome to Supabase retrain_log table either way
- Reset clean row counter and drift flag after retraining

Supabase tables for monitoring:
- anomalies: id, timestamp, features (JSONB), z_scores (JSONB), flagged_features, low_confidence_prediction
- drift_log: id, timestamp, feature, training_mean, rolling_mean, deviation_pct
- retrain_log: id, timestamp, trigger_reason, old_model_r2, new_model_r2, model_replaced (bool), rows_used

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
- On each tick: get next row from test.csv (Dec 16 – Jan 2) → scale features → call predict_full → store result + per-appliance actuals in Supabase
- If Supabase write fails: log the error, skip the tick, do not crash
- Scheduler replays test split rows chronologically (cycling); no sensor env vars needed

## Frontend conventions
- Pure HTML + JavaScript — no React, no Vue, no build step
- Tailwind CSS via CDN for styling
- index.html — landing page with tier selection
- simple.html — Basic tier form: lights input + T1 input + location input
- dashboard.html — Smart Home tier: shows live auto-updating predictions every 15 minutes
- forecast.html — 7-day forecast and monthly bill projection
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
- Raise HTTPException with correct status code â€” nothing else
- 400 bad input, 422 validation error, 500 model error
- Never catch exceptions silently
- Never return 200 with an error in the body

## TDD rules
- Write the failing test first. Confirm it fails. Then implement.
- Every function that transforms data or calls the model has a test
- A test that passes before implementation exists is wrong â€” fix the test

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
- If multiple interpretations exist, present them â€” do not pick silently
- If something is unclear, stop and ask
- Surface tradeoffs before choosing an approach
