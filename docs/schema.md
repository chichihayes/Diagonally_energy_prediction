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

## model_simple — Basic Tier (7 input features)

Trained on a reduced feature set for homeowners with no room sensors.

| Feature | Type | Unit | Source |
|---|---|---|---|
| lights | int | Wh | Manual input |
| T1 | float | °C | Manual input (main room thermometer) |
| T_out | float | °C | OpenWeatherMap (auto-fetched by location) |
| RH_out | float | % | OpenWeatherMap |
| Windspeed | float | m/s | OpenWeatherMap |
| Visibility | float | km | OpenWeatherMap |
| Tdewpoint | float | °C | OpenWeatherMap |

---

## API Output Shape (both tiers)

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
