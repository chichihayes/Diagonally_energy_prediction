# CLAUDE.md â€” Diagonally Energy Prediction

## What this app is
Diagonally Energy Prediction is a machine learning system that predicts electricity
consumption in real time. It ingests time-series energy data, engineers features,
trains a regression model, and exposes predictions via a REST API. The goal is to
provide accurate, low-latency electricity usage forecasts for integration into
energy management dashboards or third-party platforms.

## Stack
- Language: Python 3.11
- API: FastAPI + Uvicorn
- ML: scikit-learn (Random Forest / XGBoost)
- Data: pandas, numpy
- Model persistence: joblib
- Dataset: UCI ElectricityLoadDiagrams 2011-2014
- Testing: pytest + httpx
- CI: GitHub Actions

## Environment variables
```
MODEL_PATH=src/model/trained/model.joblib
API_HOST=0.0.0.0
API_PORT=8000
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
â”œâ”€â”€ data/
â”‚   â”œâ”€â”€ raw/                         # original UCI dataset (LD2011_2014.txt)
â”‚   â””â”€â”€ processed/                   # engineered features (features.csv)
â”œâ”€â”€ notebooks/                       # EDA and experimentation
â”œâ”€â”€ src/
â”‚   â”œâ”€â”€ api/
â”‚   â”‚   â”œâ”€â”€ main.py                  # FastAPI app entry point
â”‚   â”‚   â””â”€â”€ routes.py                # prediction routes
â”‚   â”œâ”€â”€ model/
â”‚   â”‚   â”œâ”€â”€ train.py                 # train and save model
â”‚   â”‚   â”œâ”€â”€ predict.py               # load model and run inference
â”‚   â”‚   â””â”€â”€ trained/                 # saved model files (gitignored)
â”‚   â””â”€â”€ services/
â”‚       â”œâ”€â”€ features.py              # feature engineering pipeline
â”‚       â””â”€â”€ data_loader.py           # load and preprocess raw data
â”œâ”€â”€ tests/
â”‚   â”œâ”€â”€ test_api.py                  # API endpoint tests
â”‚   â”œâ”€â”€ test_features.py             # feature engineering tests
â”‚   â””â”€â”€ test_model.py                # model prediction tests
â”œâ”€â”€ scripts/
â”‚   â”œâ”€â”€ download_data.py             # fetch dataset
â”‚   â””â”€â”€ run_training.py              # trigger model training
â””â”€â”€ .github/workflows/
    â””â”€â”€ ci.yml                       # run tests on push
```

## ML conventions
- Always load the model once at startup using a global singleton â€” never reload per request
- Feature engineering must be identical at training time and inference time
- All feature names must match exactly between train.py and predict.py
- Never pull all rows into memory for prediction â€” accept feature dict, return float
- Model files go in src/model/trained/ and are gitignored
- Retrain by running scripts/run_training.py â€” never retrain inside the API

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
