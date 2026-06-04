# CLAUDE.md — Diagonally Energy Prediction

## What this app is
Diagonally Energy Prediction is a machine learning system that predicts household
energy consumption for a UK home using the REFIT Smart Home Dataset (House 1).
It covers 9 individual appliances (Fridge, ChestFreezer, UprightFreezer, TumbleDryer,
WashingMachine, Dishwasher, Computer, Television, ElectricHeater) over the period
October 9 2013 – July 10 2015 (638 days, with a 41-day sensor gap in March-April 2014).

The system trains a RandomForest model on 11 lag/calendar/temperature features to
predict daily household energy consumption. It serves single-day predictions and
7-day rolling forecasts via a FastAPI backend. Every prediction is stored in Supabase.
A lightweight HTML + JavaScript frontend lets users input lag values and see the
predicted Wh, kWh, and estimated cost in GBP (£).

## Stack
- Language: Python 3.11
- API: FastAPI + Uvicorn
- Forecast Model: RandomForest (300 trees, depth 10) with 11 features — 16.6% MAPE on 9 strategic test days
- Data: pandas, numpy, scikit-learn
- Model persistence: joblib
- Dataset: REFIT Smart Home Dataset — House 1 (data/raw/House_1.csv, Oct 2013 – Jul 2015, 638 days, 8-second intervals)
- Frontend: HTML + JavaScript (no framework, no build step) + Tailwind CSS via CDN
- Database: Supabase (Postgres) — stores forecast requests (inputs + predictions)
- Cost calculation: Ofgem UK tariff rate (GBP) applied to predicted kWh
- Testing: pytest
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
│   ├── raw/                              # House_1.csv + temperature_loughborough.csv (gitignored)
│   └── processed/                        # train.csv and test.csv (gitignored)
├── notebooks/                            # EDA, model comparison, feature importance
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
│   │   ├── train_forecast.py             # train RandomForest, evaluate on 9 test days, save model
│   │   ├── forecast.py                   # forecast model singleton + inference functions
│   │   └── trained/
│   │       ├── model_forecast.joblib     # trained RandomForest in _TreeWrapper (gitignored)
│   │       ├── model_evaluation.json     # MAE/RMSE/MAPE + per-day breakdown
│   │       └── demo_day.json             # held-out demo day features + actual_wh (2015-02-10)
│   └── services/
│       ├── features.py                   # build_lag_matrix for forecast training
│       ├── data_loader.py                # load and preprocess House_1.csv → daily aggregates
│       ├── cost.py                       # Wh → kWh → GBP conversion
│       └── database.py                   # Supabase insert helpers (service role key)
├── tests/
│   ├── conftest.py                       # TestClient + mock Supabase setup
│   ├── test_api.py                       # endpoint tests
│   ├── test_forecast.py                  # forecast function tests
│   ├── test_features.py                  # lag matrix tests
│   ├── test_cost.py                      # Wh → GBP conversion tests
│   └── test_database.py                  # Supabase insert tests
├── scripts/
│   ├── run_training_forecast.py          # full offline pipeline: preprocess → train → evaluate
│   └── seed_supabase.py                  # seed forecast_requests from test split
└── .github/workflows/
    └── ci.yml                            # run all tests on push to main
```

## ML conventions

Forecast Model:
- Single model: RandomForest (300 trees, depth 10) with 11 features
- Features: day_of_week, month, is_weekend, lag_1, lag_7, rolling_mean_7, heater_lag_1, heater_lag_7, heater_rolling_mean_7, temp_mean_c, temp_min_c
- Trained on all data minus 9 strategic test days (3 LOW / 3 MID / 3 HIGH) and 1 demo day
- Evaluation: MAE, RMSE, MAPE on 9 strategic test days — 16.6% MAPE, results stored per-day
- Model saved as model_forecast.joblib (wrapped in _TreeWrapper); metrics in model_evaluation.json
- Forecast horizons: single day (POST /forecast/predict) and 7 days ahead (GET /forecast/7d)
- Confidence interval: ±15% of predicted_wh (lower_wh = ×0.85, upper_wh = ×1.15)
- Never expose raw model output to the API — always format into clean JSON
- forecast.py loads the model once at startup as a singleton
- Retrain by running scripts/run_training_forecast.py — never retrain inside the API

Weekly Bill Estimation:
- Pure calculation — no ML model involved
- Formula: projected_week_bill = sum(7-day forecast_kwh) × ELECTRICITY_TARIFF_GBP_PER_KWH
- Return optimistic (lower_wh), most_likely (predicted_wh), pessimistic (upper_wh) weekly bill
- Always read tariff from ELECTRICITY_TARIFF_GBP_PER_KWH environment variable
- Round all GBP values to 2 decimal places
- Response key: projected_week_bill with fields: optimistic_gbp, most_likely_gbp, pessimistic_gbp, period ("7 days")

## Database conventions
- Always use supabase-py client — never raw psycopg2
- Always use SUPABASE_SERVICE_ROLE_KEY for writes (bypasses RLS)
- DB writes: supabase.table('forecast_requests').insert({}).execute()
- RLS enabled on all tables
- forecast_requests table stores: id, created_at, input_date, lag inputs, temp inputs, predicted_wh, predicted_kwh, estimated_cost_gbp
- Never store raw model files or training data in Supabase

## Cost calculation conventions
- Always convert Wh to kWh before applying tariff: predicted_kwh = predicted_wh / 1000
- Tariff rate comes from environment variable ELECTRICITY_TARIFF_GBP_PER_KWH
- Never hardcode the tariff rate inside any function — always read from env
- Formula: estimated_cost_gbp = predicted_kwh * ELECTRICITY_TARIFF_GBP_PER_KWH
- Round cost to 2 decimal places before returning in API response

## Frontend conventions
- Pure HTML + JavaScript — no React, no Vue, no build step
- Tailwind CSS via CDN for styling
- forecast.html — single-day prediction form (all 11 features visible), result card shows Wh, kWh, cost, temperature
- dashboard.html — placeholder, no backend wired yet
- app.js makes fetch() calls to the FastAPI API — no direct Supabase calls from frontend
- All API responses display: predicted Wh, predicted kWh, estimated cost in GBP (£)
- Frontend is served as static files via FastAPI at /frontend — no separate server needed
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
