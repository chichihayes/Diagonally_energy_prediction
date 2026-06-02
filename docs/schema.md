# docs/schema.md — Diagonally Energy Prediction

## Dataset

| Property | Value |
|---|---|
| Source | UCI Appliances Energy Prediction |
| File | `data/raw/KAG_energydata_complete.csv` |
| Rows | 19,735 |
| Interval | Every 10 minutes |
| Missing values | None |
| Target | `Appliances` (Wh) |

---

## Raw Dataset Columns

| Column | Type | Unit | Notes |
|---|---|---|---|
| date | string | — | Timestamp — dropped at preprocessing |
| Appliances | int | Wh | TARGET — total appliance energy use |
| lights | int | Wh | Light energy use (input feature) |
| T1 | float | °C | Temperature, kitchen |
| RH_1 | float | % | Humidity, kitchen |
| T2 | float | °C | Temperature, living room |
| RH_2 | float | % | Humidity, living room |
| T3 | float | °C | Temperature, laundry room |
| RH_3 | float | % | Humidity, laundry room |
| T4 | float | °C | Temperature, office room |
| RH_4 | float | % | Humidity, office room |
| T5 | float | °C | Temperature, bathroom |
| RH_5 | float | % | Humidity, bathroom |
| T6 | float | °C | Temperature, outside building (north) |
| RH_6 | float | % | Humidity, outside building (north) |
| T7 | float | °C | Temperature, ironing room |
| RH_7 | float | % | Humidity, ironing room |
| T8 | float | °C | Temperature, teenager room 2 |
| RH_8 | float | % | Humidity, teenager room 2 |
| T9 | float | °C | Temperature, parents room |
| RH_9 | float | % | Humidity, parents room |
| T_out | float | °C | Outside temperature (weather station) |
| Press_mm_hg | float | mm Hg | Air pressure |
| RH_out | float | % | Outside humidity |
| Windspeed | float | m/s | Wind speed |
| Visibility | float | km | Visibility |
| Tdewpoint | float | °C | Dew point temperature |
| rv1 | float | — | Random noise — dropped at preprocessing |
| rv2 | float | — | Random noise — dropped at preprocessing |

---

## model_full — Smart Home Tier (25 input features)

Trained on all sensor + weather features after dropping `date`, `rv1`, `rv2`, and the `Appliances` target.

| Feature | Type | Unit | Source |
|---|---|---|---|
| lights | int | Wh | Zigbee sensor |
| T1 | float | °C | Zigbee sensor |
| RH_1 | float | % | Zigbee sensor |
| T2 | float | °C | Zigbee sensor |
| RH_2 | float | % | Zigbee sensor |
| T3 | float | °C | Zigbee sensor |
| RH_3 | float | % | Zigbee sensor |
| T4 | float | °C | Zigbee sensor |
| RH_4 | float | % | Zigbee sensor |
| T5 | float | °C | Zigbee sensor |
| RH_5 | float | % | Zigbee sensor |
| T6 | float | °C | Zigbee sensor |
| RH_6 | float | % | Zigbee sensor |
| T7 | float | °C | Zigbee sensor |
| RH_7 | float | % | Zigbee sensor |
| T8 | float | °C | Zigbee sensor |
| RH_8 | float | % | Zigbee sensor |
| T9 | float | °C | Zigbee sensor |
| RH_9 | float | % | Zigbee sensor |
| T_out | float | °C | OpenWeatherMap |
| Press_mm_hg | float | mm Hg | OpenWeatherMap |
| RH_out | float | % | OpenWeatherMap |
| Windspeed | float | m/s | OpenWeatherMap |
| Visibility | float | km | OpenWeatherMap |
| Tdewpoint | float | °C | OpenWeatherMap |

---

## API Output Shape

| Field | Type | Unit | Description |
|---|---|---|---|
| predicted_wh | float | Wh | Raw model output |
| predicted_kwh | float | kWh | predicted_wh / 1000 |
| estimated_cost_ngn | float | NGN | predicted_kwh × NERC_TARIFF_NGN_PER_KWH |

---

## Supabase — predictions table

| Column | Type | Notes |
|---|---|---|
| id | uuid | Primary key, auto-generated |
| tier | text | `'full'` or `'simple'` |
| predicted_wh | float | — |
| predicted_kwh | float | — |
| estimated_cost_ngn | float | — |
| location | text | Nullable — city name supplied by Basic tier |
| inputs | jsonb | Feature values submitted to the model |
| created_at | timestamptz | Auto-set on insert |

---

## Forecast Output Schema
| Field | Type | Description |
|---|---|---|
| ds | datetime | Forecast timestamp |
| yhat | float | Predicted consumption in Wh |
| yhat_lower | float | Lower confidence bound in Wh |
| yhat_upper | float | Upper confidence bound in Wh |
| predicted_kwh | float | yhat converted to kWh |
| estimated_cost_ngn | float | Cost in NGN at NERC tariff rate |
| optimistic_bill_ngn | float | Month bill using yhat_lower |
| pessimistic_bill_ngn | float | Month bill using yhat_upper |
| most_likely_bill_ngn | float | Month bill using yhat |

## Supabase — drift_log table

| Column           | Type        | Notes                                       |
|---|---|---|
| id               | uuid        | Primary key, auto-generated                 |
| timestamp        | timestamptz | Auto-set on insert                          |
| drift_detected   | bool        | True if any feature exceeded 15% deviation  |
| drifted_features | text[]      | Feature names that exceeded threshold       |
| deviations       | jsonb       | Feature → deviation_pct for all 25 features |
| clean_row_count  | int         | Number of clean readings in this window     |

---

## Supabase — anomalies table

| Column | Type | Notes |
|---|---|---|
| id | uuid | Primary key, auto-generated |
| timestamp | timestamptz | Time the reading was flagged |
| tier | text | `'full'` or `'simple'` |
| input_features | jsonb | All feature values submitted to the model |
| z_scores | jsonb | Z-Score per feature (only features with std > 0) |
| flagged_features | text[] | Feature names where abs(Z) > 3 |
| low_confidence_prediction | bool | Always true for rows in this table |

---

## Supabase — retrain_log table

| Column | Type | Notes |
|---|---|---|
| id | uuid | Primary key, default gen_random_uuid() |
| timestamp | timestamptz | default now() |
| trigger_reason | text | Human-readable summary of why triggered |
| old_model_r2 | float8 | R² of model before retraining |
| new_model_r2 | float8 | R² of best model from this run |
| model_replaced | boolean | True if new file written |
| rows_used | int4 | Total rows (UCI + clean Supabase) used |

---

## Model Leaderboard Schema
| Field | Type | Description |
|---|---|---|
| model | string | Model name |
| r2 | float | R² score (regression models) |
| mape | float | MAPE score (forecast models) |
| winner | boolean | True if this model was selected |
