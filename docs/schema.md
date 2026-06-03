# docs/schema.md — Diagonally Energy Prediction

## Dataset

| Property | Value |
|---|---|
| Source | REFIT Smart Home Dataset — House 1 |
| File | `data/raw/House1.csv` |
| Date range | October 9 2013 – January 2 2014 |
| Raw interval | Every 8 seconds |
| Processed interval | Every 10 minutes (resampled via mean) |
| Target | `aggregate_wh` (sum of 9 appliances, Wh) |

---

## Train / Test Split

| Split | Date range | ~Rows (after resampling + lag) |
|---|---|---|
| Train | Oct 9 – Dec 15 2013 (67 days) | ~9,000 |
| Test | Dec 16 2013 – Jan 2 2014 (18 days) | ~2,400 |

Split is **chronological — never shuffled**.

---

## Raw Dataset Columns

| Column | Type | Unit | Notes |
|---|---|---|---|
| Unix | int | s | Unix timestamp — dropped at preprocessing |
| Aggregate | float | W | Raw aggregate — dropped; we compute our own |
| Appliance1 | float | W | → renamed to Fridge |
| Appliance2 | float | W | → renamed to ChestFreezer |
| Appliance3 | float | W | → renamed to UprightFreezer |
| Appliance4 | float | W | → renamed to TumbleDryer |
| Appliance5 | float | W | → renamed to WashingMachine |
| Appliance6 | float | W | → renamed to Dishwasher |
| Appliance7 | float | W | → renamed to Computer |
| Appliance8 | float | W | → renamed to Television |
| Appliance9 | float | W | → renamed to ElectricHeater |

---

## Processed Columns (train.csv / test.csv)

### Per-appliance (Wh after 10-min resample)
Fridge, ChestFreezer, UprightFreezer, TumbleDryer, WashingMachine,
Dishwasher, Computer, Television, ElectricHeater

### Aggregate
| Column | Type | Notes |
|---|---|---|
| aggregate_wh | float | Sum of all 9 appliances — TARGET for regression and forecast |

### Time features (UK hours)
| Column | Values | Notes |
|---|---|---|
| hour | 0–23 | Hour of day (UK local time) |
| day_of_week | 0–6 | 0=Monday |
| month | 1–12 | Calendar month |
| is_weekend | 0/1 | 1 if Saturday or Sunday |
| is_night | 0/1 | 1 if hour >= 22 or hour < 6 |
| is_peak_hour | 0/1 | 1 if 16 <= hour <= 20 (UK peak demand) |

### Lag features (on aggregate_wh)
| Column | Shift | Notes |
|---|---|---|
| lag_1 | 1 interval (10 min ago) | |
| lag_6 | 6 intervals (1 hr ago) | |
| lag_144 | 144 intervals (24 hr ago) | |
| lag_1008 | 1008 intervals (1 week ago) | |

### Rolling features (on aggregate_wh)
| Column | Window | Notes |
|---|---|---|
| rolling_mean_6 | 6 intervals | Mean of last 1 hour |
| rolling_mean_144 | 144 intervals | Mean of last 24 hours |
| rolling_std_6 | 6 intervals | Std dev of last 1 hour |

---

## MODEL_FEATURES (13 input features)
hour, day_of_week, month, is_weekend, is_night, is_peak_hour,
lag_1, lag_6, lag_144, lag_1008,
rolling_mean_6, rolling_mean_144, rolling_std_6

All 13 features are StandardScaler-transformed at training time.
Scaler saved as `src/model/trained/scaler.joblib`.

---

## API Output Shape

| Field | Type | Unit | Description |
|---|---|---|---|
| predicted_wh | float | Wh | Raw model output (aggregate) |
| predicted_kwh | float | kWh | predicted_wh / 1000 |
| estimated_cost_gbp | float | GBP | predicted_kwh × ELECTRICITY_TARIFF_GBP_PER_KWH |

### Forecast Output — projected_week_bill (GET /api/v1/forecast/7d)

| Field | Type | Description |
|---|---|---|
| optimistic_weekly_gbp | float | Optimistic 7-day cost in GBP (sum of lower_wh / 1000 × tariff) |
| most_likely_weekly_gbp | float | Most likely 7-day cost in GBP (sum of predicted_wh / 1000 × tariff) |
| pessimistic_weekly_gbp | float | Pessimistic 7-day cost in GBP (sum of upper_wh / 1000 × tariff) |
| period | string | Always "7 days" |

---

## Supabase — predictions table

| Column | Type | Notes |
|---|---|---|
| id | uuid | Primary key, auto-generated |
| tier | text | Always `'full'` |
| predicted_wh | float | Model-predicted aggregate |
| predicted_kwh | float | — |
| estimated_cost_gbp | float | Cost in GBP |
| aggregate_wh | float | Actual aggregate from test split row |
| fridge_wh | float | Actual from test split row |
| chest_freezer_wh | float | — |
| upright_freezer_wh | float | — |
| tumble_dryer_wh | float | — |
| washing_machine_wh | float | — |
| dishwasher_wh | float | — |
| computer_wh | float | — |
| television_wh | float | — |
| electric_heater_wh | float | — |
| input_features | jsonb | Unscaled MODEL_FEATURES dict |
| low_confidence | bool | True if any feature Z-score > 3 |
| anomaly | bool | Alias for low_confidence |
| created_at | timestamptz | Auto-set on insert |

---

## Supabase — forecast table

| Column | Type | Notes |
|---|---|---|
| id | uuid | Primary key, auto-generated |
| created_at | timestamptz | Auto-set on insert |
| ds | timestamptz | Forecast timestamp |
| yhat | float | Predicted aggregate Wh |
| yhat_lower | float | Lower confidence bound |
| yhat_upper | float | Upper confidence bound |
| predicted_kwh | float | yhat / 1000 |
| estimated_cost_gbp | float | Cost in GBP |

---

## Supabase — drift_log table

| Column | Type | Notes |
|---|---|---|
| id | uuid | Primary key |
| timestamp | timestamptz | — |
| drift_detected | bool | True if any feature exceeded 15% deviation |
| drifted_features | text[] | Feature names that exceeded threshold |
| deviations | jsonb | Feature → deviation_pct for all MODEL_FEATURES |
| clean_row_count | int | Number of clean readings in this window |

---

## Supabase — anomalies table

| Column | Type | Notes |
|---|---|---|
| id | uuid | Primary key |
| timestamp | timestamptz | — |
| tier | text | Always `'full'` |
| input_features | jsonb | Unscaled MODEL_FEATURES |
| z_scores | jsonb | Z-Score per feature |
| flagged_features | text[] | Features where abs(Z) > 3 |
| low_confidence_prediction | bool | Always true |

---

## Supabase — retrain_log table

| Column | Type | Notes |
|---|---|---|
| id | uuid | Primary key |
| timestamp | timestamptz | — |
| trigger_reason | text | — |
| old_model_r2 | float8 | — |
| new_model_r2 | float8 | — |
| model_replaced | boolean | — |
| rows_used | int4 | — |

---

## Forecast Leaderboard Schema (forecast_leaderboard.json)
| Field | Type | Description |
|---|---|---|
| model | string | Model name (Chronos, MSTL, XGBoost_lags) |
| mae | float | Mean Absolute Error on test split |
| rmse | float | Root Mean Squared Error on test split |
| mape | float | MAPE on test split |
| winner | boolean | True if this model was selected |
