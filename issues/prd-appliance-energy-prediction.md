# PRD — Diagonally Appliance Energy Prediction

## 1. Problem Statement

Homeowners struggle to understand and predict their household appliance energy consumption before their electricity bill arrives. They have no way to anticipate how room temperature, humidity, and weather conditions translate into energy costs. This system gives homeowners an accurate prediction of appliance energy consumption in watt-hours — either automatically via Zigbee sensors (Smart Home tier) or manually via a two-field form (Basic tier) — so they can take action before costs grow.

---

## 2. Users and Roles

| User | Role |
|---|---|
| Homeowner — Smart Home | Has Zigbee sensors installed in every room. Receives automatic predictions every 15 minutes with no manual input. |
| Homeowner — Basic | Has no sensors. Enters lights usage and one room temperature manually. Sees a prediction within seconds. |

---

## 3. Solution Overview

Two prediction tiers served by one FastAPI backend:

- **Smart Home tier** — APScheduler submits Zigbee sensor readings (T1–T9, RH_1–RH_9) automatically every 15 minutes. The API enriches them with live OpenWeatherMap weather data and runs them through `model_full.joblib` (26 features, Random Forest or XGBoost — best performer). Result is stored in Supabase and displayed on the dashboard.

- **Basic tier** — Homeowner enters `lights` (Wh), `T1` (°C), and their city name. The API fetches weather automatically, assembles 7 features, and runs them through `model_simple.joblib`. Result and prediction history are shown on the frontend.

Both tiers convert predicted Wh to kWh and calculate an estimated cost in Nigerian Naira using the NERC electricity tariff rate (stored in an environment variable).

---

## 4. Happy Path

### Tier A — Smart Home

1. Homeowner installs Zigbee sensors in each room (T1–T9, RH_1–RH_9).
2. Sensors collect readings every 10 minutes automatically.
3. APScheduler fires every 15 minutes and submits the latest readings to `POST /api/v1/predict/full`.
4. The API fetches outside weather (T_out, RH_out, Windspeed, Visibility, Tdewpoint, Press_mm_hg) from OpenWeatherMap using the homeowner's location. Response is cached for 10 minutes.
5. All 26 features are assembled and passed to `model_full.joblib`.
6. Model returns predicted appliance consumption in watt-hours.
7. API converts Wh to kWh and calculates estimated cost in NGN using NERC tariff rate.
8. Prediction and cost are stored in the Supabase `predictions` table.
9. Homeowner opens the frontend dashboard and sees predicted consumption and estimated cost in NGN — updated automatically every 15 minutes, no manual input required.

### Tier B — Basic

1. Homeowner opens the frontend on their phone or browser.
2. They enter three values: `lights` (Wh), `T1` (°C), and their city name.
3. They click Submit.
4. The API fetches outside weather for their location from OpenWeatherMap (cached 10 minutes).
5. 7 features are assembled and passed to `model_simple.joblib`.
6. Model returns predicted appliance consumption in watt-hours.
7. API converts Wh to kWh and calculates estimated cost in NGN using NERC tariff rate.
8. Prediction and cost are stored in Supabase.
9. Homeowner sees: predicted consumption (Wh and kWh), estimated electricity cost in NGN, which weather conditions are influencing the prediction, and their full prediction history.

---

## 5. Out of Scope

- User authentication — no login or registration for the demo.
- Appliance-level breakdown — one total consumption number only, not per appliance.
- Automated model retraining — model is trained once offline; no retraining pipeline.
- Solar or renewable energy integration — grid consumption only.
- Alerts and notifications — no email or SMS on high consumption.

---

## 6. Acceptance Criteria

| # | Criterion |
|---|---|
| AC-01 | `POST /api/v1/predict/full` accepts all 26 features and returns `predicted_wh`, `predicted_kwh`, and `estimated_cost_ngn` within 2 seconds. |
| AC-02 | `POST /api/v1/predict/simple` accepts `lights`, `T1`, and `location` and returns the same three fields within 2 seconds. |
| AC-03 | All six regression models (Random Forest, XGBoost, LightGBM, CatBoost, Extra Trees, Ridge Regression) trained and evaluated — best R² on held-out test split saved as final model achieving at least 85% R². |
| AC-04 | OpenWeatherMap responses are cached for 10 minutes — no duplicate API calls within the cache window. |
| AC-05 | APScheduler submits Smart Home readings to `/api/v1/predict/full` every 15 minutes without manual intervention. |
| AC-06 | Every prediction and cost estimate is stored in Supabase immediately after the API responds. |
| AC-07 | NERC tariff rate is read from an environment variable — not hardcoded anywhere in the codebase. |
| AC-08 | The frontend is fully responsive on mobile and desktop with no build step (Tailwind via CDN). |
| AC-09 | Basic tier frontend displays: predicted Wh, predicted kWh, estimated NGN cost, top contributing weather factors, and prediction history. |
| AC-10 | All tests pass in CI on every push to main. |
| AC-11 | `GET /health` returns `{ "status": "ok" }` at all times. |
| AC-12 | All six regression models trained, evaluated and compared — best R² saved as final model. |
| AC-13 | All five time series models trained, evaluated and compared — best MAPE saved as final model. |
| AC-14 | GET /api/v1/models/leaderboard returns full comparison table of all models with scores and winner. |
| AC-15 | GET /api/v1/forecast/24h returns hourly forecast with confidence intervals and estimated NGN cost per hour. |
| AC-16 | GET /api/v1/forecast/7d returns daily forecast with peak day, lowest day and projected monthly bill range. |
| AC-17 | forecast.html displays 7-day forecast chart, highlights peak days and shows optimistic and pessimistic monthly bill. |
| AC-18 | Monthly bill projection returns optimistic, pessimistic and most likely NGN values. |
| AC-19 | Every incoming reading is checked with Z-Score — any feature with Z > 3 is flagged as anomaly and stored in Supabase anomalies table with low_confidence=True on the prediction. |
| AC-20 | Every 100 clean readings rolling mean deviation is calculated for all 25 features using formula: abs(rolling_mean - training_mean) / training_mean × 100 — any feature > 15% triggers drift flag logged to drift_log table. |
| AC-21 | Retraining triggers automatically when all 3 conditions met: drift detected, 2000+ clean rows, anomaly rate < 10%. New model only replaces old if R² improves. Outcome logged to retrain_log. |
| AC-22 | training_stats.json saved at training time containing mean and std of all 25 features — used as fixed reference for Z-Score and drift detection. |

---

## 7. Module Map

```
src/
├── api/
│   ├── main.py                       # FastAPI app + APScheduler startup
│   └── routes.py                     # all prediction and forecast endpoints
├── model/
│   ├── train_full.py                 # train all 6 regression models on 25 features — save best R²
│   ├── train_simple.py               # train all 6 regression models on 7 features — save best R²
│   ├── train_forecast.py             # train all 5 time series models — save best MAPE
│   ├── evaluate.py                   # compare all models, print leaderboard, return best
│   ├── predict.py                    # load regression model singletons and run inference
│   ├── forecast.py                   # load forecast model singleton and return predictions
│   └── trained/
│       ├── model_full.joblib         # best regression model on 25 features
│       ├── model_simple.joblib       # best regression model on 7 features
│       └── model_forecast.joblib     # best time series model
└── services/
    ├── features.py                   # assemble feature dicts for both tiers + lag features
    ├── data_loader.py                # load and preprocess KAG_energydata_complete.csv
    ├── weather.py                    # OpenWeatherMap client with 10-min cache
    ├── cost.py                       # Wh to NGN conversion + monthly bill projection
    ├── database.py                   # Supabase insert and retrieve predictions and forecasts
    └── scheduler.py                  # APScheduler — auto-submit readings every 15 minutes

frontend/
├── index.html                        # landing page with tier selection
├── simple.html                       # Basic tier form and results
├── dashboard.html                    # Smart Home tier live dashboard
└── forecast.html                     # 7-day forecast and monthly bill projection

scripts/
├── run_training_full.py              # train all regression models, save best for full tier
├── run_training_simple.py            # train all regression models, save best for simple tier
└── run_training_forecast.py          # train all time series models, save best forecast model

tests/
├── test_api.py                       # endpoint tests for all routes
├── test_features.py                  # feature assembly and lag feature tests
├── test_model.py                     # regression model inference tests
├── test_forecast.py                  # time series forecast tests
├── test_evaluate.py                  # model comparison and leaderboard tests
├── test_weather.py                   # weather client and cache tests
├── test_cost.py                      # cost calculation and bill projection tests
└── test_database.py                  # Supabase storage tests
```

---

## 8. Implementation Decisions

| Decision | Choice | Reason |
|---|---|---|
| Regression models | Random Forest, XGBoost, LightGBM, CatBoost, Extra Trees, Ridge Regression — best R² wins | Comprehensive evaluation ensures objectively best model selected for tabular regression |
| Time series models | Prophet, XGBoost with lags, LightGBM with lags, LSTM, TFT — best MAPE wins | Covers classical, boosting and deep learning approaches — TFT is state of the art |
| Two regression model files | model_full.joblib (25 features), model_simple.joblib (7 features) | Basic tier users have no sensors — simpler model gives meaningful predictions |
| Dataset | UCI Appliances Energy Prediction (KAG_energydata_complete.csv) | 19,735 rows, 28 features, real Zigbee sensor data, 10-minute intervals, no missing values |
| rv1 and rv2 dropped | Dropped at preprocessing | Random noise variables — no predictive value confirmed by feature importance |
| Weather | OpenWeatherMap free tier | Supplies 6 outside features automatically, cached 10 minutes |
| Database | Supabase (Postgres) | Stores all predictions and forecasts after every API call |
| Scheduler | APScheduler inside FastAPI | Simple deployment for demo — submits Smart Home readings every 15 minutes |
| Cost calculation | NERC tariff from env var | Rate can change without redeploy |
| Bill projection | Optimistic, most likely, pessimistic range | Realistic picture using confidence intervals from forecast model |
| Frontend | HTML + JS + Tailwind CDN | No build step, mobile responsive, zero framework overhead |
| Model persistence | joblib | Standard for scikit-learn, fast load, singleton pattern at startup |
| Deep learning | neuralforecast + PyTorch | Unified API for LSTM and TFT — reduces boilerplate |
