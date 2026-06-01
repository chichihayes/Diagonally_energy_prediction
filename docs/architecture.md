# docs/architecture.md — Diagonally Energy Prediction

## File Structure

```
diagonally-energy-prediction/
├── data/
│   ├── raw/                              # KAG_energydata_complete.csv (gitignored)
│   └── processed/                        # engineered features + lag features
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
│   │   ├── main.py                       # FastAPI app init, APScheduler startup
│   │   └── routes.py                     # all route handlers
│   ├── model/
│   │   ├── train_full.py                 # train all 6 regression models on 25 features
│   │   ├── train_simple.py               # train all 6 regression models on 7 features
│   │   ├── train_forecast.py             # train all 5 time series models
│   │   ├── evaluate.py                   # compare models, return best by metric
│   │   ├── predict.py                    # regression model singletons + inference
│   │   ├── forecast.py                   # forecast model singleton + inference
│   │   └── trained/                      # model_full.joblib, model_simple.joblib,
│   │                                     # model_forecast.joblib (gitignored)
│   └── services/
│       ├── features.py                   # assemble feature dicts + lag features
│       ├── data_loader.py                # load CSV, drop rv1/rv2/date, split train/test
│       ├── weather.py                    # OpenWeatherMap client, 10-min in-memory cache
│       ├── cost.py                       # Wh→kWh, NGN cost, monthly bill projection
│       ├── database.py                   # Supabase insert and retrieve helpers
│       └── scheduler.py                  # APScheduler — fires every 15 min
├── scripts/
│   ├── run_training_full.py              # offline entrypoint for full regression training
│   ├── run_training_simple.py            # offline entrypoint for simple regression training
│   └── run_training_forecast.py          # offline entrypoint for time series training
├── tests/
│   ├── test_api.py
│   ├── test_features.py
│   ├── test_model.py
│   ├── test_forecast.py
│   ├── test_evaluate.py
│   ├── test_weather.py
│   ├── test_cost.py
│   └── test_database.py
├── notebooks/
└── .github/workflows/ci.yml
```

---

## Data Flow — Training (offline)

```
data/raw/KAG_energydata_complete.csv
    ↓
data_loader.py          # load CSV, drop date/rv1/rv2, split 80/20 time-ordered
    ↓
features.py             # produce full matrix (25 cols), simple matrix (7 cols),
                        # and lag feature matrix (lag_1h, lag_24h, lag_168h,
                        # rolling_mean_3h, rolling_mean_24h)
    ↓
train_full.py           # fit RF, XGBoost, LightGBM, CatBoost, ExtraTrees, Ridge
                        # evaluate R² on test split → save best as model_full.joblib
train_simple.py         # same 6 models on 7-feature set
                        # evaluate R² → save best as model_simple.joblib
train_forecast.py       # fit Prophet, XGBoost+lags, LightGBM+lags, LSTM, TFT
                        # evaluate MAPE → save best as model_forecast.joblib
    ↓
evaluate.py             # compare all models, print leaderboard
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
cost.py                 # Wh→kWh, kWh × ELECTRICITY_TARIFF_NGN_PER_KWH → NGN
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
cost.py                 # Wh→kWh, kWh × tariff → NGN
    ↓
database.py             # insert row into Supabase predictions table
    ↓
JSON response           # { predicted_wh, predicted_kwh, estimated_cost_ngn,
                        #   weather_factors }
    ↓
simple.html             # display result + prediction history
```

---

## Data Flow — Forecast (runtime)

```
GET /api/v1/forecast/24h  or  GET /api/v1/forecast/7d  (?location=Lagos)
    ↓
weather.py              # fetch current outside conditions (cached 10 min)
    ↓
forecast.py             # model_forecast singleton → yhat, yhat_lower, yhat_upper
                        # for each hour (24h) or each day (7d)
    ↓
cost.py                 # convert each yhat to NGN cost
                        # sum forecast kWh → projected monthly bill
                        # return optimistic / most_likely / pessimistic NGN
    ↓
JSON response           # { forecast[], peak_hour/day, lowest_hour/day,
                        #   projected_month_bill }
    ↓
forecast.html           # 7-day chart, peak days, bill range
```

---

## Service Boundaries

| Layer | Responsibility | Must not |
|---|---|---|
| `routes.py` | Validate input, call services, return HTTP response | Contain business logic or ML calls |
| `features.py` | Assemble feature dicts from raw inputs + weather, build lag features | Fetch weather or call the model |
| `weather.py` | Fetch and cache OpenWeatherMap data | Know anything about the model or DB |
| `predict.py` | Load regression models once at startup, run inference | Reload model per request, touch DB |
| `forecast.py` | Load forecast model once at startup, run inference | Reload model per request, touch DB |
| `cost.py` | Convert Wh→kWh→NGN, calculate bill projection | Know anything about models or weather |
| `database.py` | Insert and retrieve prediction/forecast rows from Supabase | Know anything about models or weather |
| `evaluate.py` | Compare model scores, return winner — offline only | Run inside the API process |
| `train_*.py` | Train, evaluate, and save models — offline only | Run inside the API process |

---

## Key Constraints

- All three model files are loaded once at startup as module-level singletons — never reloaded per request.
- Feature column names in `features.py` must match exactly between training and inference.
- Weather responses are cached in memory for 10 minutes to keep predictions under 2 seconds.
- APScheduler runs inside the FastAPI process, started in the `main.py` lifespan event.
- Training is always run offline via `scripts/` — never triggered from within the API.
- `ELECTRICITY_TARIFF_NGN_PER_KWH` must always be read from the environment — never hardcoded.
