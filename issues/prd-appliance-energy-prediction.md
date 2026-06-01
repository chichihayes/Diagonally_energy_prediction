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
| AC-03 | The best of Random Forest and XGBoost achieves ≥ 85% accuracy (R²) on the held-out test split of the UCI dataset. |
| AC-04 | OpenWeatherMap responses are cached for 10 minutes — no duplicate API calls within the cache window. |
| AC-05 | APScheduler submits Smart Home readings to `/api/v1/predict/full` every 15 minutes without manual intervention. |
| AC-06 | Every prediction and cost estimate is stored in Supabase immediately after the API responds. |
| AC-07 | NERC tariff rate is read from an environment variable — not hardcoded anywhere in the codebase. |
| AC-08 | The frontend is fully responsive on mobile and desktop with no build step (Tailwind via CDN). |
| AC-09 | Basic tier frontend displays: predicted Wh, predicted kWh, estimated NGN cost, top contributing weather factors, and prediction history. |
| AC-10 | All tests pass in CI on every push to main. |
| AC-11 | `GET /health` returns `{ "status": "ok" }` at all times. |

---

## 7. Module Map

```
src/
├── api/
│   ├── main.py                  # FastAPI app, APScheduler startup
│   └── routes.py                # POST /predict/full, POST /predict/simple, GET /health
├── model/
│   ├── train.py                 # train RF and XGBoost, evaluate, save best model
│   ├── predict.py               # load model singleton, run inference
│   └── trained/
│       ├── model_full.joblib    # 26-feature model (Smart Home)
│       └── model_simple.joblib  # 7-feature model (Basic)
└── services/
    ├── features.py              # assemble feature dicts for both tiers
    ├── data_loader.py           # load and preprocess KAG_energydata_complete.csv
    ├── weather.py               # OpenWeatherMap client with 10-min cache
    └── database.py              # Supabase insert for predictions table

frontend/
├── index.html                   # Basic tier form and results display
└── dashboard.html               # Smart Home tier live dashboard

scripts/
└── run_training.py              # offline training entrypoint

tests/
├── test_api.py                  # endpoint tests (httpx)
├── test_features.py             # feature assembly tests
├── test_model.py                # model inference tests
└── test_weather.py              # weather client and cache tests
```

---

## 8. Implementation Decisions

| Decision | Choice | Reason |
|---|---|---|
| ML models | Random Forest (baseline) + XGBoost (challenger) | Both trained and evaluated; best R² on test split is saved. RF handles multicollinearity across 28 correlated T/RH features without scaling. XGBoost typically outperforms on tabular data. |
| Two model files | `model_full.joblib` (26 features), `model_simple.joblib` (7 features) | Basic tier users have no sensors — a simpler model trained on a minimal feature set gives meaningful predictions without requiring all 26 inputs. |
| Dataset | UCI Appliances Energy Prediction (KAG_energydata_complete.csv) | 19,735 rows, 28 features, real Zigbee sensor data from a Belgian house, 10-minute intervals, no missing values, CSV format. |
| rv1 / rv2 dropped | Dropped at preprocessing | Random noise variables added by dataset authors to test model robustness. No predictive value. |
| lights kept as input | Input feature, not label | Raw sensor reading separate from the Appliances target. |
| Weather | OpenWeatherMap free tier | Supplies T_out, RH_out, Windspeed, Visibility, Tdewpoint, Press_mm_hg automatically. Responses cached 10 minutes to keep predictions under 2 seconds. |
| Database | Supabase (Postgres) | Stores all predictions and sensor readings after every API call. Managed Postgres with a simple REST client. |
| Scheduler | APScheduler | Runs inside the FastAPI process on startup; submits Smart Home readings every 15 minutes. |
| Cost calculation | NERC tariff from env var | Rate can change without a redeploy. Applied to predicted kWh. |
| Frontend | HTML + JS + Tailwind CDN | No build step, mobile responsive, zero framework overhead for a demo. |
| Model persistence | joblib | Standard for scikit-learn, fast load of numpy arrays. Loaded once at startup as a singleton — never reloaded per request. |
