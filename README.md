# Diagonally Energy Prediction

ML system that predicts household appliance energy consumption for a UK home using the
[REFIT Smart Home Dataset](https://pureportal.strath.ac.uk/en/datasets/refit-electrical-load-measurements-cleaned)
(House 1, Oct 2013 – Jan 2014).

## What it does

- Trains a Random Forest forecast model (300 trees, depth 10, 11 features including temperature)
  on 9-appliance aggregate consumption data, evaluated on 9 strategic test days (~19% MAPE)
- Runs an APScheduler background job every 15 minutes replaying the held-out test split
  (Dec 16 – Jan 2 2014), storing per-appliance actuals and estimated GBP cost in Supabase
- Serves a REST API for 24-hour and 7-day forecasts, prediction history, model leaderboard,
  drift status, and retraining status
- Flags anomalous readings (Z-Score > 3 on any of 13 features) and marks predictions
  as `low_confidence`
- Detects drift every 100 clean readings and triggers automatic retraining when 3 conditions
  are all met: drift detected, ≥ 2000 clean rows, anomaly rate < 10%
- Serves a pure HTML + JavaScript frontend (no build step) with live dashboard,
  7-day forecast chart, and monthly bill projection in GBP (£)

## Stack

| Layer | Tech |
|---|---|
| Language | Python 3.11 |
| API | FastAPI + Uvicorn |
| Models | Random Forest with temperature features (scikit-learn) |
| Data | pandas, numpy, scikit-learn |
| Model persistence | joblib |
| Dataset | REFIT Smart Home Dataset — House 1 |
| Frontend | HTML + JavaScript + Tailwind CSS (CDN) |
| Database | Supabase (Postgres) |
| Scheduler | APScheduler |
| Tests | pytest + httpx |
| CI | GitHub Actions |

## Setup

```bash
python -m venv venv
venv\Scripts\activate       # Windows
# source venv/bin/activate  # macOS/Linux
pip install -r requirements.txt
cp .env.example .env        # fill in SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_SERVICE_ROLE_KEY
```

Place the REFIT House1.csv dataset at `data/raw/House1.csv` before training.

## Train the forecast model

```bash
python scripts/run_training_forecast.py
```

This trains Random Forest on all data minus 9 strategic test days, evaluates MAE/RMSE/MAPE
on those 9 days, saves the model to `src/model/trained/model_forecast.joblib`, and writes
`src/model/trained/forecast_leaderboard.json`.

## Run the API

```bash
uvicorn src.api.main:app --reload
```

The scheduler starts automatically and begins replaying test split rows every 15 minutes.

## Run tests

```bash
pytest tests/
```

## API routes

| Method | Route | Description |
|---|---|---|
| GET | `/api/v1/predictions` | Stored prediction history (filterable by tier, limit, since) |
| GET | `/api/v1/forecast/24h` | Hourly consumption forecast for the next 24 hours |
| GET | `/api/v1/forecast/7d` | Daily forecast for next 7 days + weekly bill projection |
| GET | `/api/v1/models/leaderboard` | MAE/RMSE/MAPE for RandomForest on 9 strategic test days |
| GET | `/api/v1/monitor/drift` | Latest drift check result |
| GET | `/api/v1/monitor/retrain` | Latest retraining outcome |
| GET | `/health` | Health check |

## Environment variables

See [`docs/env.md`](docs/env.md) for the full reference.

```
MODEL_PATH_FORECAST=src/model/trained/model_forecast.joblib
API_HOST=0.0.0.0
API_PORT=8000
SUPABASE_URL=
SUPABASE_ANON_KEY=
SUPABASE_SERVICE_ROLE_KEY=
ELECTRICITY_TARIFF_GBP_PER_KWH=0.34
```

## Docs

| File | Contents |
|---|---|
| [`docs/schema.md`](docs/schema.md) | Dataset schema, Supabase table definitions |
| [`docs/api-contracts.md`](docs/api-contracts.md) | Every route, request shape, response shape |
| [`docs/architecture.md`](docs/architecture.md) | File structure, data flow, service boundaries |
| [`docs/decisions.md`](docs/decisions.md) | Architectural decision records |
| [`docs/env.md`](docs/env.md) | Environment variables reference |
