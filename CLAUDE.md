# CLAUDE.md â€” Diagonally Energy Prediction

## What this app is
Diagonally Energy Prediction is a machine learning system that helps homeowners 
predict their household appliance energy consumption in real time. It supports two tiers:

Tier A — Smart Home: Zigbee sensors installed in each room automatically collect 
room temperatures (T1-T9) and humidity readings (RH_1-RH_9). Outside weather 
features (T_out, RH_out, Windspeed, Visibility, Tdewpoint, Press_mm_hg) are 
auto-fetched from OpenWeatherMap API. The homeowner only inputs lights usage. 
All 26 features are submitted to POST /api/v1/predict/full and the model returns 
the predicted appliance energy consumption in watt-hours. This is the most accurate tier.

Tier B — Basic: No sensors needed. The homeowner inputs only lights usage and 
one room temperature (T1). All outside weather features are auto-fetched from 
OpenWeatherMap API using the homeowner's location. 7 features total are submitted 
to POST /api/v1/predict/simple and the model returns a predicted appliance energy 
consumption in watt-hours. Less accurate but accessible to any homeowner.

The goal of both tiers is to help homeowners identify energy-hungry patterns, 
understand what drives their appliance consumption, and take action to reduce 
their electricity bills before they arrive.

The system also includes a lightweight HTML + JavaScript frontend where homeowners 
can enter their readings and see their predicted consumption and estimated electricity 
cost in Nigerian Naira instantly. Every prediction is stored in Supabase so the 
homeowner can view their consumption history. A scheduler automatically submits 
sensor readings to the API every 15 minutes for Smart Home tier users so no manual 
input is needed.

## Stack
- Language: Python 3.11
- API: FastAPI + Uvicorn
- ML: scikit-learn (Random Forest / XGBoost)
- Data: pandas, numpy
- Model persistence: joblib
- Dataset: UCI Appliances Energy Prediction (19,735 rows, 28 features, CSV format)
- Weather API: OpenWeatherMap (free tier) — supplies T_out, RH_out, Windspeed, Visibility, Tdewpoint, Press_mm_hg for both tiers
- Frontend: HTML + JavaScript (no framework, no build step) + Tailwind CSS via CDN
- Database: Supabase (Postgres) — stores all predictions and sensor readings
- Scheduler: APScheduler — submits readings to API every 15 minutes automatically
- Cost calculation: NERC tariff rate applied to predicted kWh to return estimated cost in NGN
- Testing: pytest + httpx
- CI: GitHub Actions

## Environment variables
```
MODEL_PATH_FULL=src/model/trained/model_full.joblib
MODEL_PATH_SIMPLE=src/model/trained/model_simple.joblib
API_HOST=0.0.0.0
API_PORT=8000
OPENWEATHERMAP_API_KEY=
SUPABASE_URL=
SUPABASE_ANON_KEY=
SUPABASE_SERVICE_ROLE_KEY=
ELECTRICITY_TARIFF_NGN_PER_KWH=68.00
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
│   ├── raw/                         # original UCI dataset (KAG_energydata_complete.csv)
│   └── processed/                   # cleaned and engineered features
├── notebooks/                       # EDA and experimentation
├── frontend/
│   ├── index.html                   # main homeowner dashboard
│   ├── simple.html                  # basic tier input form
│   ├── full.html                    # smart home tier input form
│   └── assets/
│       ├── style.css                # custom styles
│       └── app.js                   # API calls and UI logic
├── src/
│   ├── api/
│   │   ├── main.py                  # FastAPI app entry point
│   │   └── routes.py                # /predict/full and /predict/simple endpoints
│   ├── model/
│   │   ├── train_full.py            # train model on all 26 features
│   │   ├── train_simple.py          # train model on 7 features only
│   │   ├── predict.py               # load both models and run inference
│   │   └── trained/                 # saved model files (gitignored)
│   └── services/
│       ├── features.py              # feature engineering pipeline
│       ├── data_loader.py           # load and preprocess raw CSV
│       ├── weather.py               # fetch outside weather from OpenWeatherMap
│       ├── cost.py                  # convert predicted Wh to NGN cost using tariff rate
│       ├── database.py              # Supabase client — store and retrieve predictions
│       └── scheduler.py             # APScheduler — auto-submit readings every 15 minutes
├── tests/
│   ├── test_api.py                  # API endpoint tests for both tiers
│   ├── test_features.py             # feature engineering tests
│   ├── test_model.py                # model prediction tests
│   ├── test_weather.py              # weather service mock tests
│   ├── test_cost.py                 # cost calculation tests
│   └── test_database.py             # Supabase storage tests
├── scripts/
│   ├── run_training_full.py         # trigger full model training
│   └── run_training_simple.py       # trigger simple model training
└── .github/workflows/
    └── ci.yml                       # run tests on push
```

## ML conventions
- Always load both models once at startup using global singletons — never reload per request
- Feature engineering must be identical at training time and inference time for each tier
- Full model feature names: lights, T1, RH_1, T2, RH_2, T3, RH_3, T4, RH_4, T5, RH_5, T6, RH_6, T7, RH_7, T8, RH_8, T9, RH_9, T_out, Press_mm_hg, RH_out, Windspeed, Visibility, Tdewpoint
- Simple model feature names: lights, T1, T_out, RH_out, Windspeed, Visibility, Tdewpoint
- rv1 and rv2 are always dropped at preprocessing — they are random noise variables
- Never pull all rows into memory for prediction — accept feature dict, return float
- Model files go in src/model/trained/ and are gitignored
- Retrain by running scripts/run_training_full.py or run_training_simple.py — never retrain inside the API
- weather.py fetches outside features using homeowner location — always cache the weather response for 10 minutes to avoid hitting API rate limits

## Database conventions
- Always use supabase-py client — never raw psycopg2
- DB reads: supabase.table('predictions').select('*').execute()
- DB writes: supabase.table('predictions').insert({}).execute()
- RLS enabled on all tables — every request must pass the correct key
- predictions table stores: id, timestamp, tier, input_features (JSON), 
  predicted_wh, predicted_kwh, estimated_cost_ngn, location
- Never store raw model files or training data in Supabase

## Cost calculation conventions
- Always convert Wh to kWh before applying tariff: predicted_kwh = predicted_wh / 1000
- Tariff rate comes from environment variable ELECTRICITY_TARIFF_NGN_PER_KWH
- Never hardcode the tariff rate inside any function — always read from env
- Formula: estimated_cost_ngn = predicted_kwh * ELECTRICITY_TARIFF_NGN_PER_KWH
- Round cost to 2 decimal places before returning in API response

## Scheduler conventions
- APScheduler runs as a background service inside the FastAPI app
- Interval: every 15 minutes
- On each tick: fetch latest sensor readings → call predict/full internally → 
  store result in Supabase predictions table
- If OpenWeatherMap call fails: log the error, skip the tick, do not crash
- If Supabase write fails: log the error, skip the tick, do not crash
- Scheduler only runs for Smart Home tier — Basic tier is always manual input

## Frontend conventions
- Pure HTML + JavaScript — no React, no Vue, no build step
- Tailwind CSS via CDN for styling
- index.html — landing page showing latest prediction and consumption history
- simple.html — Basic tier form: lights input + T1 input + location input
- full.html — Smart Home tier: shows live auto-updating predictions every 15 minutes
- app.js makes fetch() calls to the FastAPI API — no direct Supabase calls from frontend
- All API responses display: predicted Wh, predicted kWh, estimated cost in NGN
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
