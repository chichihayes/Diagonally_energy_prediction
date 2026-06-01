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

## Stack
- Language: Python 3.11
- API: FastAPI + Uvicorn
- ML: scikit-learn (Random Forest / XGBoost)
- Data: pandas, numpy
- Model persistence: joblib
- Dataset: UCI Appliances Energy Prediction (19,735 rows, 28 features, CSV format)
- Weather API: OpenWeatherMap (free tier) — supplies T_out, RH_out, Windspeed, Visibility, Tdewpoint, Press_mm_hg for both tiers
- Testing: pytest + httpx
- CI: GitHub Actions

## Environment variables
```
MODEL_PATH_FULL=src/model/trained/model_full.joblib
MODEL_PATH_SIMPLE=src/model/trained/model_simple.joblib
API_HOST=0.0.0.0
API_PORT=8000
OPENWEATHERMAP_API_KEY=
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
├── src/
│   ├── api/
│   │   ├── main.py                  # FastAPI app entry point
│   │   └── routes.py                # /predict/full and /predict/simple endpoints
│   ├── model/
│   │   ├── train_full.py            # train model on all 26 features
│   │   ├── train_simple.py          # train model on 7 features only
│   │   ├── predict.py               # load model and run inference for both tiers
│   │   └── trained/                 # saved model files (gitignored)
│   └── services/
│       ├── features.py              # feature engineering pipeline
│       ├── data_loader.py           # load and preprocess raw CSV
│       └── weather.py               # fetch outside weather from OpenWeatherMap
├── tests/
│   ├── test_api.py                  # API endpoint tests for both tiers
│   ├── test_features.py             # feature engineering tests
│   ├── test_model.py                # model prediction tests
│   └── test_weather.py              # weather service mock tests
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
