# docs/architecture.md — Diagonally Energy Prediction

## File Structure

```
diagonally-energy-prediction/
├── data/
│   ├── raw/                              # House_1.csv (REFIT Smart Home Dataset, gitignored)
│   │   └── temperature_loughborough.csv  # cached daily temps from Open-Meteo (gitignored)
│   └── processed/                        # train.csv and test.csv (gitignored)
├── frontend/
│   ├── dashboard.html                    # placeholder — no backend wired yet
│   ├── forecast.html                     # single-day prediction form + result card
│   └── assets/
│       ├── style.css                     # custom styles
│       └── app.js                        # forecast form logic and API calls
├── src/
│   ├── api/
│   │   ├── main.py                       # FastAPI app entry point, mounts /frontend static
│   │   └── routes.py                     # forecast and evaluation endpoints
│   ├── model/
│   │   ├── train_forecast.py             # train RandomForest on train.csv, evaluate on 9 test days
│   │   ├── forecast.py                   # forecast model singleton + inference functions
│   │   └── trained/
│   │       ├── model_forecast.joblib     # trained RandomForest wrapped in _TreeWrapper (gitignored)
│   │       ├── model_evaluation.json     # MAE/RMSE/MAPE + per-day breakdown for 9 test days
│   │       └── demo_day.json             # held-out demo day features + actual_wh (2015-02-10)
│   └── services/
│       ├── features.py                   # build_lag_matrix for forecast training
│       ├── data_loader.py                # load and preprocess House_1.csv → daily aggregates
│       ├── cost.py                       # Wh → kWh → GBP conversion
│       └── database.py                   # Supabase insert helpers
├── scripts/
│   ├── run_training_forecast.py          # full offline pipeline: preprocess → train → evaluate
│   └── seed_supabase.py                  # seed forecast_requests from test split
├── tests/
│   ├── conftest.py                       # TestClient + mock Supabase setup
│   ├── test_api.py                       # endpoint tests
│   ├── test_forecast.py                  # forecast function tests
│   ├── test_features.py                  # lag matrix tests
│   ├── test_cost.py                      # Wh → GBP conversion tests
│   └── test_database.py                  # Supabase insert tests
├── notebooks/                            # EDA, model comparison
└── .github/workflows/ci.yml             # run all tests on push to main
```

---

## Data Flow — Training (offline)

```
data/raw/House_1.csv
    ↓
data_loader.py          # load CSV → resample to 10-min → aggregate to daily
                        # add lag features (lag_1, lag_7, rolling_mean_7 for aggregate + heater)
                        # merge temperature from temperature_loughborough.csv (or Open-Meteo API)
                        # split: train.csv (all days except 9 test + 1 demo)
                        #        test.csv  (9 strategic test days: 3 LOW / 3 MID / 3 HIGH)
                        #        demo_day.json (held-out 2015-02-10 features + actual_wh)
    ↓
train_forecast.py       # build_lag_matrix on train.csv
                        # fit RandomForest (300 trees, depth 10, random_state=42)
                        # evaluate MAE/RMSE/MAPE on 9 test days (per-day + aggregate)
                        # save model → model_forecast.joblib (_TreeWrapper wrapping RF)
                        # save metrics → model_evaluation.json (includes per_day array)
```

---

## Data Flow — Single-day forecast (runtime)

```
User fills form → POST /api/v1/forecast/predict
    ↓
routes.py               # validate ForecastPredictRequest (7 user inputs + optional temps)
    ↓
forecast.py             # forecast_single_day():
                        #   - build 11-feature row from inputs + date derivations + temps
                        #   - if temp not provided: fetch from Open-Meteo API
                        #   - model.predict_from_features(row) → predicted_wh
                        #   - × tariff / 1000 → estimated_cost_gbp
    ↓
database.py             # insert_forecast_request → Supabase forecast_requests table
    ↓
JSON response           # { date, predicted_wh, predicted_kwh, estimated_cost_gbp,
                        #   lower_wh, upper_wh, temp_mean_c, temp_min_c }
    ↓
forecast.html           # result card: date, cost, Wh, kWh, temperature
```

---

## Data Flow — 7-day rolling forecast (runtime)

```
GET /api/v1/forecast/7d
    ↓
forecast.py             # forecast_7d():
                        #   - recursive multi-step: seeds from last known train data
                        #   - fetches 7-day temps from Open-Meteo forecast API
                        #   - predicts 7 days ahead, confidence interval ±15%
    ↓
JSON response           # { forecast[7], peak_day, lowest_day, projected_week_bill }
```

---

## Data Flow — Model evaluation (runtime)

```
GET /api/v1/models/evaluation
    ↓
routes.py               # read src/model/trained/model_evaluation.json from disk
    ↓
JSON response           # { model, mae, rmse, mape, evaluation, per_day[] }
```

---

## Service Boundaries

| Layer | Responsibility | Must not |
|---|---|---|
| `routes.py` | Validate input, call services, return HTTP response | Contain business logic or ML calls |
| `features.py` | Build lag feature matrix from daily aggregate_wh | Call the model or touch DB |
| `data_loader.py` | Load and preprocess House_1.csv to daily aggregates, manage train/test split | Know anything about models |
| `forecast.py` | Load forecast model once at startup, run inference | Reload model per request, touch DB |
| `cost.py` | Convert Wh → kWh → GBP | Know anything about models or weather |
| `database.py` | Insert rows into Supabase tables | Know anything about models or features |
| `train_forecast.py` | Train RandomForest, evaluate on 9 test days, save model — offline only | Run inside the API process |

---

## Key Constraints

- `model_forecast.joblib` is loaded once at startup as a module-level singleton in `forecast.py` — never reloaded per request.
- Temperature is fetched from Open-Meteo API per prediction; if the user supplies `temp_mean_c`/`temp_min_c` directly those are used instead.
- `ELECTRICITY_TARIFF_GBP_PER_KWH` must always be read from the environment — never hardcoded.
- Training is always run offline via `scripts/run_training_forecast.py` — never triggered from within the API.
- `dashboard.html` has no wired backend — it requires a `GET /api/v1/readings` endpoint and read path from Supabase which is not yet implemented.
