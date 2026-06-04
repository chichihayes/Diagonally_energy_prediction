# docs/schema.md — Diagonally Energy Prediction

## Dataset

| Property | Value |
|---|---|
| Source | REFIT Smart Home Dataset — House 1 |
| File | `data/raw/House_1.csv` |
| Date range | October 9 2013 – July 10 2015 (638 days, with a 41-day sensor gap in March–April 2014) |
| Raw interval | Every 8 seconds |
| Processed interval | Resampled to 10-minute means, then aggregated to daily totals |
| Target | `aggregate_wh` (sum of 9 appliances per day, Wh) |

---

## Forecast Model — 9 Strategic Test Days

The RandomForest is trained on all daily data **except** these 9 held-out dates:

| Tier | Dates |
|---|---|
| LOW  | 2013-10-16, 2014-12-07, 2015-01-03 |
| MID  | 2014-07-21, 2014-11-12, 2014-08-01 |
| HIGH | 2013-11-22, 2013-12-12, 2014-01-19 |

Test days span the full date range and cover seasonal and consumption variation.

Demo day (held out from both train and test): **2015-02-10** — stored in `demo_day.json`.

---

## Raw Dataset Columns

| Column | Type | Unit | Notes |
|---|---|---|---|
| Unix | int | s | Unix timestamp — converted to UK-local datetime index, then dropped |
| Aggregate | float | W | Raw aggregate — dropped; we compute our own sum |
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

### Per-appliance (Wh — daily total after 10-min resample and daily sum)
Fridge, ChestFreezer, UprightFreezer, TumbleDryer, WashingMachine,
Dishwasher, Computer, Television, ElectricHeater

### Aggregate
| Column | Type | Notes |
|---|---|---|
| aggregate_wh | float | Sum of all 9 appliances per day — TARGET for forecast model |

### Calendar features
| Column | Values | Notes |
|---|---|---|
| day_of_week | 0–6 | 0 = Monday |
| month | 1–12 | Calendar month |
| is_weekend | 0/1 | 1 if Saturday or Sunday |

### Lag features (on daily aggregate_wh)
| Column | Shift | Notes |
|---|---|---|
| lag_1 | 1 day | Yesterday's total |
| lag_7 | 7 days | Same day last week |
| rolling_mean_7 | 7-day rolling mean | Shifted by 1 to avoid leakage |

### Heater lag features (on daily ElectricHeater)
| Column | Shift | Notes |
|---|---|---|
| heater_lag_1 | 1 day | Yesterday's heater total |
| heater_lag_7 | 7 days | Heater same day last week |
| heater_rolling_mean_7 | 7-day rolling mean | Shifted by 1 to avoid leakage |

### Temperature features (merged from Open-Meteo / temperature_loughborough.csv)
| Column | Notes |
|---|---|
| temp_mean_c | Daily mean temperature at Loughborough, UK |
| temp_min_c | Daily minimum temperature |

---

## MODEL_FEATURES (11 input features)

```
day_of_week, month, is_weekend,
lag_1, lag_7, rolling_mean_7,
heater_lag_1, heater_lag_7, heater_rolling_mean_7,
temp_mean_c, temp_min_c
```

No scaling applied — RandomForest is scale-invariant.

---

## API Output Shape — POST /api/v1/forecast/predict

| Field | Type | Unit | Description |
|---|---|---|---|
| predicted_wh | float | Wh | Raw model output |
| predicted_kwh | float | kWh | predicted_wh / 1000 |
| estimated_cost_gbp | float | GBP | predicted_kwh × ELECTRICITY_TARIFF_GBP_PER_KWH |
| lower_wh | float | Wh | predicted_wh × 0.85 (optimistic bound) |
| upper_wh | float | Wh | predicted_wh × 1.15 (pessimistic bound) |
| temp_mean_c | float | °C | Temperature used for this prediction |
| temp_min_c | float | °C | Min temperature used for this prediction |

## API Output Shape — GET /api/v1/forecast/7d projected_week_bill

| Field | Type | Description |
|---|---|---|
| optimistic_gbp | float | Sum of lower_wh / 1000 × tariff over 7 days |
| most_likely_gbp | float | Sum of predicted_wh / 1000 × tariff over 7 days |
| pessimistic_gbp | float | Sum of upper_wh / 1000 × tariff over 7 days |
| period | string | Always `"7 days"` |

---

## Supabase — forecast_requests table

Stores every user-initiated prediction via POST /api/v1/forecast/predict.

| Column | Type | Notes |
|---|---|---|
| id | uuid | Primary key, auto-generated |
| created_at | timestamptz | Auto-set on insert |
| input_date | text | Date the user wants to forecast (YYYY-MM-DD) |
| lag_1 | float8 | Yesterday's total household consumption (Wh) |
| lag_7 | float8 | Consumption 7 days ago (Wh) |
| rolling_mean_7 | float8 | Average daily consumption over past 7 days (Wh) |
| heater_lag_1 | float8 | Yesterday's electric heater usage (Wh) |
| heater_lag_7 | float8 | Heater usage 7 days ago (Wh) |
| heater_rolling_mean_7 | float8 | Average daily heater usage over past 7 days (Wh) |
| temp_mean_c | float8 | Mean temperature used for prediction |
| temp_min_c | float8 | Min temperature used for prediction |
| predicted_wh | float8 | Model-predicted aggregate consumption |
| predicted_kwh | float8 | predicted_wh / 1000 |
| estimated_cost_gbp | float8 | Cost in GBP |

---

## model_evaluation.json schema

| Field | Type | Description |
|---|---|---|
| model | string | Always `"RandomForest"` |
| mae | float | Mean Absolute Error on 9 strategic test days (Wh) |
| rmse | float | Root Mean Squared Error (Wh) |
| mape | float | MAPE on 9 strategic test days (%) |
| evaluation | string | `"9 strategic test days (3 LOW / 3 MID / 3 HIGH)"` |
| per_day | array | Per-day breakdown: Band, Date, Temp C, Actual Wh, Predicted Wh, Error % |

---

## demo_day.json schema

Holds the feature values and actual consumption for the held-out demo day (2015-02-10).
Used to pre-fill the forecast form with realistic values.

| Field | Type | Notes |
|---|---|---|
| date | string | Always `"2015-02-10"` |
| day_of_week | int | 1 (Tuesday) |
| month | int | 2 |
| is_weekend | int | 0 |
| lag_1 | float | Yesterday's aggregate Wh |
| lag_7 | float | 7 days ago aggregate Wh |
| rolling_mean_7 | float | 7-day rolling mean Wh |
| heater_lag_1 | float | Yesterday's heater Wh |
| heater_lag_7 | float | Heater 7 days ago Wh |
| heater_rolling_mean_7 | float | Heater 7-day rolling mean Wh |
| temp_mean_c | float | 2.2 |
| temp_min_c | float | 0.8 |
| actual_wh | float | 11020.83 — ground truth for this day |
