# docs/api-contracts.md — Diagonally Energy Prediction

## POST /api/v1/predict/full

Smart Home tier. Accepts all 25 input features. Weather is fetched
automatically from OpenWeatherMap — do not pass T_out, RH_out, etc. directly;
the API enriches the payload internally.

**Request body:**
```json
{
  "lights": 0,
  "T1": 19.89,
  "RH_1": 47.6,
  "T2": 19.2,
  "RH_2": 44.79,
  "T3": 19.79,
  "RH_3": 44.73,
  "T4": 17.17,
  "RH_4": 41.67,
  "T5": 17.2,
  "RH_5": 55.2,
  "T6": 7.03,
  "RH_6": 84.26,
  "T7": 17.2,
  "RH_7": 41.63,
  "T8": 18.2,
  "RH_8": 48.9,
  "T9": 17.03,
  "RH_9": 45.53,
  "location": "Lagos"
}
```

**Response — 200:**
```json
{
  "predicted_wh": 84.3,
  "predicted_kwh": 0.0843,
  "estimated_cost_ngn": 7.21
}
```

**Errors:**
| Code | Meaning |
|---|---|
| 400 | Missing or invalid field |
| 422 | Pydantic validation failure |
| 500 | Model inference error or weather fetch failure |

---

## POST /api/v1/predict/simple

Basic tier. Homeowner supplies only `lights`, `T1`, and `location`.
All weather data is fetched and injected automatically.

**Request body:**
```json
{
  "lights": 0,
  "T1": 19.89,
  "location": "Lagos"
}
```

**Response — 200:**
```json
{
  "predicted_wh": 60.5,
  "predicted_kwh": 0.0605,
  "estimated_cost_ngn": 5.18,
  "weather_factors": {
    "T_out": 28.4,
    "RH_out": 82.0,
    "Windspeed": 3.1,
    "Visibility": 10.0,
    "Tdewpoint": 25.1
  }
}
```

**Errors:**
| Code | Meaning |
|---|---|
| 400 | Missing or invalid field |
| 422 | Pydantic validation failure |
| 500 | Model inference error or weather fetch failure |

---

## GET /api/v1/predictions

Returns stored prediction history from Supabase ordered by most recent first.

**Query params:**
| Param | Type | Default | Description |
|---|---|---|---|
| tier | string | — | Filter by `full` or `simple` (optional) |
| limit | int | 20 | Max records to return |

**Response — 200:**
```json
[
  {
    "id": "uuid",
    "tier": "simple",
    "predicted_wh": 60.5,
    "predicted_kwh": 0.0605,
    "estimated_cost_ngn": 5.18,
    "location": "Lagos",
    "created_at": "2026-06-01T10:00:00Z"
  }
]
```

---

## GET /api/v1/forecast/24h
Returns hourly consumption forecast for next 24 hours.
Query params: location (string)
Response:
{
  forecast: [
    {
      hour: 2024-01-15 14:00,
      predicted_wh: 280.5,
      predicted_kwh: 0.28,
      lower_wh: 210.0,
      upper_wh: 350.0,
      estimated_cost_ngn: 19.04
    }
  ],
  peak_hour: 2024-01-15 20:00,
  lowest_hour: 2024-01-15 04:00
}

---

## GET /api/v1/forecast/7d
Returns daily consumption forecast for next 7 days.
Query params: location (string)
Response:
{
  forecast: [
    {
      date: 2024-01-15,
      predicted_wh: 6720.0,
      predicted_kwh: 6.72,
      lower_wh: 5040.0,
      upper_wh: 8400.0,
      estimated_cost_ngn: 456.96
    }
  ],
  peak_day: Tuesday,
  lowest_day: Wednesday,
  projected_month_bill: {
    optimistic_ngn: 3200.00,
    pessimistic_ngn: 5100.00,
    most_likely_ngn: 4200.00
  }
}

---

## GET /api/v1/models/leaderboard
Returns comparison of all trained models and which was selected.
Response:
{
  regression_full: [
    { model: RandomForest, r2: 0.87 },
    { model: XGBoost, r2: 0.91 },
    { model: LightGBM, r2: 0.90 },
    { model: CatBoost, r2: 0.89 },
    { model: ExtraTrees, r2: 0.86 },
    { model: Ridge, r2: 0.71 },
    { winner: XGBoost }
  ],
  forecast: [
    { model: Prophet, mape: 12.3 },
    { model: XGBoost_lags, mape: 10.1 },
    { model: LightGBM_lags, mape: 9.8 },
    { model: LSTM, mape: 8.9 },
    { model: TFT, mape: 7.2 },
    { winner: TFT }
  ]
}

---

## GET /health

**Response — 200:**
```json
{ "status": "ok" }
```
