# docs/api-contracts.md — Diagonally Energy Prediction

## GET /health

**Response — 200:**
```json
{ "status": "ok" }
```

---

## GET /api/v1/models/evaluation

Returns MAE/RMSE/MAPE for the RandomForest forecast model plus per-day breakdown on 9 strategic test days.

**Response — 200:**
```json
{
  "model": "RandomForest",
  "mae": 6811.17,
  "rmse": 10951.45,
  "mape": 16.6,
  "evaluation": "9 strategic test days (3 LOW / 3 MID / 3 HIGH)",
  "per_day": [
    { "Band": "HIGH", "Date": "2013-11-22", "Temp C": 4.2, "Actual Wh": 58643, "Predicted Wh": 38483, "Error %": 34.4 },
    { "Band": "HIGH", "Date": "2013-12-12", "Temp C": 7.1, "Actual Wh": 61532, "Predicted Wh": 44815, "Error %": 27.2 },
    { "Band": "HIGH", "Date": "2014-01-19", "Temp C": 5.2, "Actual Wh": 62409, "Predicted Wh": 42710, "Error %": 31.6 },
    { "Band": "LOW",  "Date": "2013-10-16", "Temp C": 9.8, "Actual Wh": 7084,  "Predicted Wh": 8454,  "Error %": 19.3 },
    { "Band": "LOW",  "Date": "2014-12-07", "Temp C": 6.1, "Actual Wh": 7006,  "Predicted Wh": 7636,  "Error %": 9.0  },
    { "Band": "LOW",  "Date": "2015-01-03", "Temp C": 3.2, "Actual Wh": 7134,  "Predicted Wh": 8419,  "Error %": 18.0 },
    { "Band": "MID",  "Date": "2014-07-21", "Temp C": 19.3,"Actual Wh": 15198, "Predicted Wh": 15006, "Error %": 1.3  },
    { "Band": "MID",  "Date": "2014-11-12", "Temp C": 10.2,"Actual Wh": 15072, "Predicted Wh": 15076, "Error %": 0.0  },
    { "Band": "MID",  "Date": "2014-08-01", "Temp C": 17.8,"Actual Wh": 15058, "Predicted Wh": 13813, "Error %": 8.3  }
  ]
}
```

**Errors:**
| Code | Meaning |
|---|---|
| 503 | model_evaluation.json not found — run scripts/run_training_forecast.py first |

---

## GET /api/v1/forecast/7d

Returns daily consumption forecast for the next 7 days with weekly bill projection.
Seeds from the last 7 days of training data; fetches temperatures from Open-Meteo forecast API.

**Response — 200:**
```json
{
  "forecast": [
    {
      "date": "2026-06-04",
      "predicted_wh": 15831.6,
      "predicted_kwh": 15.8316,
      "lower_wh": 13456.9,
      "upper_wh": 18206.3,
      "estimated_cost_gbp": 5.38
    }
  ],
  "peak_day": "Tuesday",
  "lowest_day": "Saturday",
  "projected_week_bill": {
    "optimistic_gbp": 28.50,
    "most_likely_gbp": 33.20,
    "pessimistic_gbp": 38.10,
    "period": "7 days"
  }
}
```

**Errors:**
| Code | Meaning |
|---|---|
| 500 | Forecast model not loaded or prediction error |

---

## POST /api/v1/forecast/predict

Single-day prediction from user-supplied lag features.
Temperature is auto-fetched from Open-Meteo if not provided.
Saves the request + result to the `forecast_requests` Supabase table.

**Request:**
```json
{
  "date": "2015-02-10",
  "lag_1": 10638.64,
  "lag_7": 14785.26,
  "rolling_mean_7": 20023.43,
  "heater_lag_1": 143.97,
  "heater_lag_7": 143.99,
  "heater_rolling_mean_7": 143.94,
  "temp_mean_c": 2.2,
  "temp_min_c": 0.8
}
```

`temp_mean_c` and `temp_min_c` are optional — omit them and the backend fetches temperature automatically.

**Response — 200:**
```json
{
  "date": "2015-02-10",
  "predicted_wh": 15831.6,
  "predicted_kwh": 15.8316,
  "estimated_cost_gbp": 5.38,
  "lower_wh": 13456.9,
  "upper_wh": 18206.3,
  "temp_mean_c": 2.2,
  "temp_min_c": 0.8
}
```

**Errors:**
| Code | Meaning |
|---|---|
| 500 | Model not loaded or prediction error |
