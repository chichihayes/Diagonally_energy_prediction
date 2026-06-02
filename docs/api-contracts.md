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
  "estimated_cost_ngn": 7.21,
  "low_confidence": false
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
  },
  "low_confidence": false
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

Returns hourly consumption forecast for the next 24 hours.

**Query params:**
| Param | Type | Required | Description |
|---|---|---|---|
| location | string | Yes | City name (e.g. `Lagos`) |

**Response — 200:**
```json
{
  "forecast": [
    {
      "hour": "2026-06-01T14:00:00Z",
      "predicted_wh": 280.5,
      "predicted_kwh": 0.28,
      "lower_wh": 210.0,
      "upper_wh": 350.0,
      "estimated_cost_ngn": 19.04
    }
  ],
  "peak_hour": "2026-06-01T20:00:00Z",
  "lowest_hour": "2026-06-01T04:00:00Z"
}
```

**Errors:**
| Code | Meaning |
|---|---|
| 400 | Missing location param |
| 500 | Forecast model error or weather fetch failure |

---

## GET /api/v1/forecast/7d

Returns daily consumption forecast for the next 7 days with monthly bill projection.

**Query params:**
| Param | Type | Required | Description |
|---|---|---|---|
| location | string | Yes | City name (e.g. `Lagos`) |

**Response — 200:**
```json
{
  "forecast": [
    {
      "date": "2026-06-01",
      "predicted_wh": 6720.0,
      "predicted_kwh": 6.72,
      "lower_wh": 5040.0,
      "upper_wh": 8400.0,
      "estimated_cost_ngn": 456.96
    }
  ],
  "peak_day": "Tuesday",
  "lowest_day": "Wednesday",
  "projected_month_bill": {
    "optimistic_ngn": 3200.00,
    "pessimistic_ngn": 5100.00,
    "most_likely_ngn": 4200.00
  }
}
```

**Errors:**
| Code | Meaning |
|---|---|
| 400 | Missing location param |
| 500 | Forecast model error or weather fetch failure |

---

## GET /api/v1/models/leaderboard

Returns R² scores for all regression models and MAPE scores for all forecast models, with the selected winner for each.

**Response — 200:**
```json
{
  "regression_full": [
    { "model": "RandomForest", "r2": 0.87, "winner": false },
    { "model": "XGBoost", "r2": 0.91, "winner": true },
    { "model": "LightGBM", "r2": 0.90, "winner": false },
    { "model": "CatBoost", "r2": 0.89, "winner": false },
    { "model": "ExtraTrees", "r2": 0.86, "winner": false },
    { "model": "Ridge", "r2": 0.71, "winner": false }
  ],
  "forecast": [
    { "model": "Prophet", "mape": 12.3, "winner": false },
    { "model": "XGBoost_lags", "mape": 10.1, "winner": false },
    { "model": "LightGBM_lags", "mape": 9.8, "winner": false },
    { "model": "LSTM", "mape": 8.9, "winner": false },
    { "model": "TFT", "mape": 7.2, "winner": true }
  ]
}
```

**Errors:**
| Code | Meaning |
|---|---|
| 500 | Model leaderboard data unavailable |

---

## GET /health

**Response — 200:**
```json
{ "status": "ok" }
```

---

## GET /api/v1/monitor/drift

Returns the most recent drift check result from the drift_log table.

**Response — 200:**
```json
{
  "timestamp": "2026-06-01T10:00:00Z",
  "drift_detected": true,
  "drifted_features": ["T1", "RH_2"],
  "deviations": {"T1": 20.5, "RH_2": 16.1},
  "clean_row_count": 100
}
```

**Errors:**
| Code | Meaning |
|---|---|
| 404  | No drift check has been run yet |
| 500  | Failed to retrieve drift status from database |

---

## GET /api/v1/monitor/retrain

Returns the most recent retraining outcome from the retrain_log table.

**Response — 200:**
```json
{
  "timestamp": "2026-06-01T10:00:00+00:00",
  "old_model_r2": 0.75,
  "new_model_r2": 0.85,
  "model_replaced": true,
  "rows_used": 2500
}
```

**Errors:**
| Code | Meaning |
|---|---|
| 404  | No retraining has run yet |
| 500  | Supabase query error |
