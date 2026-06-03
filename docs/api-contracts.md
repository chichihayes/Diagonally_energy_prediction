# docs/api-contracts.md — Diagonally Energy Prediction

## GET /api/v1/predictions

Returns stored prediction history from Supabase ordered by most recent first.

**Query params:**
| Param | Type | Default | Description |
|---|---|---|---|
| tier | string | — | Filter by `full` (optional) |
| limit | int | 20 | Max records to return (1–50) |
| since | datetime | — | Return only records after this ISO timestamp |

**Response — 200:**
```json
[
  {
    "id": "uuid",
    "tier": "full",
    "predicted_wh": 320.5,
    "predicted_kwh": 0.3205,
    "estimated_cost_gbp": 0.11,
    "aggregate_wh": 315.0,
    "fridge_wh": 45.0,
    "chest_freezer_wh": 20.0,
    "upright_freezer_wh": 18.0,
    "tumble_dryer_wh": 0.0,
    "washing_machine_wh": 0.0,
    "dishwasher_wh": 0.0,
    "computer_wh": 80.0,
    "television_wh": 95.0,
    "electric_heater_wh": 57.0,
    "low_confidence": false,
    "created_at": "2013-12-16T09:00:00Z"
  }
]
```

---

## GET /api/v1/forecast/24h

Returns hourly consumption forecast for the next 24 hours.

**Response — 200:**
```json
{
  "forecast": [
    {
      "hour": "2013-12-17T10:00:00",
      "predicted_wh": 280.5,
      "predicted_kwh": 0.28,
      "lower_wh": 210.0,
      "upper_wh": 350.0,
      "estimated_cost_gbp": 0.10
    }
  ],
  "peak_hour": "2013-12-17T18:00:00",
  "lowest_hour": "2013-12-17T04:00:00"
}
```

**Errors:**
| Code | Meaning |
|---|---|
| 500 | Forecast model error |

---

## GET /api/v1/forecast/7d

Returns daily consumption forecast for the next 7 days with weekly bill projection.

**Response — 200:**
```json
{
  "forecast": [
    {
      "date": "2013-12-17",
      "predicted_wh": 6720.0,
      "predicted_kwh": 6.72,
      "lower_wh": 5040.0,
      "upper_wh": 8400.0,
      "estimated_cost_gbp": 2.28
    }
  ],
  "peak_day": "Tuesday",
  "lowest_day": "Wednesday",
  "projected_week_bill": {
    "optimistic_gbp": 11.50,
    "most_likely_gbp": 15.90,
    "pessimistic_gbp": 19.80,
    "period": "7 days"
  }
}
```

**Errors:**
| Code | Meaning |
|---|---|
| 500 | Forecast model error |

---

## GET /api/v1/models/leaderboard

Returns R² scores for all regression models and MAPE/MAE/RMSE scores for all forecast models.

**Response — 200:**
```json
{
  "regression": [
    { "model": "RandomForest", "r2": 0.87, "winner": false },
    { "model": "XGBoost", "r2": 0.91, "winner": true }
  ],
  "forecast": [
    { "model": "Chronos", "mae": 45.2, "rmse": 60.1, "mape": 8.5, "winner": true },
    { "model": "MSTL",    "mae": 55.0, "rmse": 72.0, "mape": 9.8, "winner": false },
    { "model": "XGBoost_lags", "mae": 60.1, "rmse": 80.5, "mape": 11.2, "winner": false }
  ]
}
```

**Errors:**
| Code | Meaning |
|---|---|
| 503 | Leaderboard file not found — run training scripts first |

---

## GET /health

**Response — 200:**
```json
{ "status": "ok" }
```

---

## GET /api/v1/monitor/drift

Returns the most recent drift check result.

**Response — 200:**
```json
{
  "timestamp": "2013-12-16T10:00:00Z",
  "drift_detected": true,
  "drifted_features": ["lag_1", "rolling_mean_6"],
  "deviations": {"lag_1": 20.5, "rolling_mean_6": 16.1},
  "clean_row_count": 100
}
```

**Errors:**
| Code | Meaning |
|---|---|
| 404 | No drift check has been run yet |
| 500 | Failed to retrieve drift status from database |

---

## GET /api/v1/monitor/retrain

Returns the most recent retraining outcome.

**Response — 200:**
```json
{
  "timestamp": "2013-12-16T10:00:00+00:00",
  "old_model_r2": 0.75,
  "new_model_r2": 0.85,
  "model_replaced": true,
  "rows_used": 2500
}
```

**Errors:**
| Code | Meaning |
|---|---|
| 404 | No retraining has run yet |
| 500 | Supabase query error |
