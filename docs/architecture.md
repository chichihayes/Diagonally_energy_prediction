# docs/architecture.md — Diagonally Energy Prediction

## File Structure

```
diagonally-energy-prediction/
├── data/
│   ├── raw/                              # House_1.csv (REFIT Smart Home Dataset, gitignored)
│   └── processed/                        # train.csv, test.csv, engineered features + lag features
├── frontend/
│   ├── dashboard.html                    # Smart Home tier live dashboard
│   ├── forecast.html                     # 7-day forecast and monthly bill projection
│   └── assets/
│       ├── style.css                     # custom styles
│       └── app.js                        # API calls and UI logic
├── src/
│   ├── api/
│   │   ├── main.py                       # FastAPI app entry point + APScheduler startup
│   │   └── routes.py                     # all prediction, forecast, and monitor endpoints
│   ├── model/
│   │   ├── train_forecast.py             # train Chronos-Bolt, MSTL, XGBoost — save best MAPE
│   │   ├── evaluate.py                   # write_leaderboard helper
│   │   ├── forecast.py                   # forecast model singleton + inference
│   │   └── trained/
│   │       ├── model_forecast.joblib     # best time series model (gitignored)
│   │       ├── forecast_leaderboard.json # MAPE scores for all 3 trained models
│   │       └── training_stats.json       # per-feature mean + std from train split (for Z-Score)
│   └── services/
│       ├── features.py                   # build_lag_matrix for forecast training
│       ├── data_loader.py                # load and preprocess House1.csv, split train/test
│       ├── cost.py                       # Wh → kWh → GBP, monthly bill projection
│       ├── database.py                   # Supabase insert and retrieve helpers
│       ├── scheduler.py                  # APScheduler — replays test split rows every 15 min
│       ├── monitor.py                    # Z-Score anomaly detection on every incoming reading
│       └── retrain_trigger.py            # drift check + retraining conditions every 100 readings
├── scripts/
│   ├── run_training_forecast.py          # offline entrypoint — train all 3 models, save best
│   └── run_retraining.py                 # retraining entrypoint — fetches clean rows, retrains
├── tests/
│   ├── test_api.py
│   ├── test_features.py
│   ├── test_model.py
│   ├── test_forecast.py
│   ├── test_evaluate.py
│   ├── test_cost.py
│   ├── test_database.py
│   ├── test_monitor.py
│   ├── test_retrain_trigger.py
│   └── test_scheduler.py
├── notebooks/
└── .github/workflows/ci.yml
```

---

## Data Flow — Training (offline)

```
data/raw/House_1.csv  (REFIT Smart Home Dataset, House 1, Oct 2013–Jul 2015)
    ↓
data_loader.py          # load CSV, drop unused columns, split 70/30 time-ordered
                        # → data/processed/train.csv, test.csv
    ↓
features.py             # build_lag_matrix: lag_1h, lag_24h, lag_168h,
                        # rolling_mean_3h, rolling_mean_24h on aggregate_wh
    ↓
train_forecast.py       # fit Chronos-Bolt (Small), MSTL, XGBoost+lags
                        # evaluate MAPE on test split
                        # save best MAPE model → model_forecast.joblib
                        # save all scores → forecast_leaderboard.json
                        # save per-feature mean+std → training_stats.json
    ↓
evaluate.py             # write_leaderboard — compares models, marks winner
```

---

## Data Flow — Scheduler tick (every 15 min, runtime)

```
APScheduler fires every 15 min
    ↓
scheduler.py            # read next row from data/processed/test.csv (Dec 29 2014–Jul 10 2015)
                        # predicted_wh = row["aggregate_wh"]  (no model inference on tick)
    ↓
cost.py                 # wh_to_cost: Wh → kWh × ELECTRICITY_TARIFF_GBP_PER_KWH → GBP
    ↓
monitor.py              # check_anomaly: Z-Score across all MODEL_FEATURES
                        # Z > 3 on any feature → is_anomaly = True, low_confidence = True
    ↓
database.py             # if anomaly: store_anomaly → Supabase anomalies table
                        # insert_prediction → Supabase predictions table
                        #   (tier, predicted_wh, predicted_kwh, estimated_cost_gbp,
                        #    per-appliance Wh columns, low_confidence, aggregate_wh)
    ↓
                        # every 100 clean (non-anomalous) readings:
retrain_trigger.py      # check_drift: rolling mean vs training mean for each feature
                        # deviation > 15% on any feature → drift_detected = True
database.py             # store_drift_event → Supabase drift_log table
retrain_trigger.py      # run_retraining_if_ready:
                        #   condition 1: drift_detected = True
                        #   condition 2: clean_row_count >= 2000
                        #   condition 3: anomaly_rate < 10%
                        # if all 3 met: retrain all 3 models via run_retraining.py
                        #   new MAPE < old MAPE → replace model_forecast.joblib
                        #   log result → Supabase retrain_log table
```

---

## Data Flow — Forecast (runtime)

```
GET /api/v1/forecast/24h   or   GET /api/v1/forecast/7d
    ↓
forecast.py             # model_forecast singleton (loaded once at startup)
                        # returns yhat, yhat_lower, yhat_upper per hour (24h) or day (7d)
    ↓
cost.py                 # convert each yhat to GBP cost
                        # 7d: sum forecast kWh → projected_week_bill
                        # return optimistic (yhat_lower) / most_likely (yhat) / pessimistic (yhat_upper)
    ↓
JSON response           # { forecast[], peak_hour/day, lowest_hour/day,
                        #   projected_week_bill (7d only) }
    ↓
forecast.html           # 7-day chart, peak days, bill range
```

---

## Data Flow — Monitor endpoints (runtime)

```
GET /api/v1/monitor/drift
    ↓
database.py             # get_latest_drift_event → Supabase drift_log table
    ↓
JSON response           # { drift_detected, drifted_features, deviations, timestamp }

GET /api/v1/monitor/retrain
    ↓
database.py             # latest row from Supabase retrain_log table
    ↓
JSON response           # { timestamp, old_mape, new_mape, model_replaced, rows_used }
```

---

## Data Flow — Predictions history (runtime)

```
GET /api/v1/predictions  (?tier=, &limit=, &since=)
    ↓
database.py             # get_predictions → Supabase predictions table
    ↓
JSON response           # list of stored prediction rows

GET /api/v1/models/leaderboard
    ↓
routes.py               # read src/model/trained/forecast_leaderboard.json from disk
    ↓
JSON response           # { forecast: [ { model, mape, mae, rmse, winner } ] }
```

---

## Service Boundaries

| Layer | Responsibility | Must not |
|---|---|---|
| `routes.py` | Validate input, call services, return HTTP response | Contain business logic or ML calls |
| `features.py` | Build lag feature matrix from aggregate_wh time series | Call the model or touch DB |
| `data_loader.py` | Load and preprocess House_1.csv, expose MODEL_FEATURES and APPLIANCE_COLS | Know anything about models |
| `forecast.py` | Load forecast model once at startup, run inference | Reload model per request, touch DB |
| `cost.py` | Convert Wh → kWh → GBP, calculate bill projection | Know anything about models or weather |
| `database.py` | Insert and retrieve all Supabase table rows | Know anything about models or features |
| `monitor.py` | Z-Score anomaly check per reading using training_stats.json | Touch DB or run the model |
| `retrain_trigger.py` | Drift check + retraining gate (3 conditions) + trigger run_retraining.py | Run inside a request; must only be called from scheduler |
| `scheduler.py` | Replay test split rows every 15 min, orchestrate monitor → DB → drift → retrain | Run inference; predicted_wh comes from aggregate_wh column directly |
| `evaluate.py` | Compare model scores, write leaderboard — offline only | Run inside the API process |
| `train_forecast.py` | Train all 3 time series models, save best — offline only | Run inside the API process |

---

## Key Constraints

- `model_forecast.joblib` is loaded once at startup as a module-level singleton in `forecast.py` — never reloaded per request.
- `training_stats.json` is loaded once at import time in `retrain_trigger.py` — provides fixed training mean/std for drift and Z-Score checks.
- APScheduler runs inside the FastAPI process, started in the `main.py` lifespan event.
- Training is always run offline via `scripts/` — never triggered from within the API directly.
- Anomalous readings are stored in Supabase but never counted toward the clean row pool or used for retraining.
- `ELECTRICITY_TARIFF_GBP_PER_KWH` must always be read from the environment — never hardcoded.
- Drift check runs every 100 clean readings (in-process counter in `scheduler.py`); retraining gate checks Supabase row counts for the 2000-row threshold.
