# docs/architecture.md — Diagonally Energy Prediction

## File Structure

```
diagonally-energy-prediction/
├── data/
│   ├── raw/                          # KAG_energydata_complete.csv (gitignored)
│   └── processed/                    # features_full.csv, features_simple.csv
├── frontend/
│   ├── index.html                    # Basic tier — form + results + history
│   └── dashboard.html                # Smart Home tier — live auto-updating dashboard
├── src/
│   ├── api/
│   │   ├── main.py                   # FastAPI app init, APScheduler startup
│   │   └── routes.py                 # all route handlers
│   ├── model/
│   │   ├── train.py                  # train RF + XGBoost, pick winner, save both models
│   │   ├── predict.py                # model singleton loader, inference functions
│   │   └── trained/                  # model_full.joblib, model_simple.joblib (gitignored)
│   └── services/
│       ├── features.py               # assemble feature dicts for full and simple tiers
│       ├── data_loader.py            # load CSV, drop rv1/rv2/date, split train/test
│       ├── weather.py                # OpenWeatherMap client, 10-min in-memory cache
│       └── database.py               # Supabase insert helper
├── scripts/
│   └── run_training.py               # offline entrypoint — calls train.py
├── tests/
│   ├── test_api.py
│   ├── test_features.py
│   ├── test_model.py
│   └── test_weather.py
├── notebooks/
└── .github/workflows/ci.yml
```

---

## Data Flow — Training (offline)

```
data/raw/KAG_energydata_complete.csv
    ↓
data_loader.py          # load CSV, drop date/rv1/rv2, split 80/20 train/test
    ↓
features.py             # produce full feature matrix (25 cols) and simple matrix (7 cols)
    ↓
train.py                # fit RF and XGBoost on each matrix
                        # evaluate R² on test split
                        # save best model as model_full.joblib / model_simple.joblib
```

---

## Data Flow — Smart Home Tier (runtime)

```
APScheduler (every 15 min)
    ↓
POST /api/v1/predict/full  (lights, T1-T9, RH_1-RH_9, location)
    ↓
weather.py              # fetch T_out, Press_mm_hg, RH_out, Windspeed, Visibility,
                        # Tdewpoint from OpenWeatherMap (cached 10 min)
    ↓
features.py             # assemble 25-feature dict
    ↓
predict.py              # model_full singleton → predicted_wh
    ↓
routes.py               # convert Wh→kWh, calculate NGN cost
    ↓
database.py             # insert row into Supabase predictions table
    ↓
JSON response           # { predicted_wh, predicted_kwh, estimated_cost_ngn }
    ↓
dashboard.html          # polls or refreshes every 15 min
```

---

## Data Flow — Basic Tier (runtime)

```
Homeowner submits form  (lights, T1, location)
    ↓
POST /api/v1/predict/simple
    ↓
weather.py              # fetch T_out, RH_out, Windspeed, Visibility, Tdewpoint
                        # from OpenWeatherMap (cached 10 min)
    ↓
features.py             # assemble 7-feature dict
    ↓
predict.py              # model_simple singleton → predicted_wh
    ↓
routes.py               # convert Wh→kWh, calculate NGN cost, attach weather_factors
    ↓
database.py             # insert row into Supabase predictions table
    ↓
JSON response           # { predicted_wh, predicted_kwh, estimated_cost_ngn,
                        #   weather_factors }
    ↓
index.html              # display result + prediction history
```

---

## Service Boundaries

| Layer | Responsibility | Must not |
|---|---|---|
| `routes.py` | Validate input, call services, return HTTP response | Contain business logic or ML calls |
| `features.py` | Assemble feature dicts from raw inputs + weather | Fetch weather or call the model |
| `weather.py` | Fetch and cache OpenWeatherMap data | Know anything about the model or DB |
| `predict.py` | Load model once at startup, run inference | Reload model per request, touch DB |
| `database.py` | Insert prediction rows into Supabase | Know anything about models or weather |
| `train.py` | Train, evaluate, and save models | Run inside the API process |

---

## Key Constraints

- Models are loaded once at startup as module-level singletons — never reloaded per request.
- Feature engineering logic in `features.py` must be identical at training time and inference time.
- All feature column names must match exactly between `train.py` and `predict.py`.
- Weather responses are cached in memory for 10 minutes to keep predictions under 2 seconds.
- APScheduler runs inside the FastAPI process, started in `main.py` lifespan event.
