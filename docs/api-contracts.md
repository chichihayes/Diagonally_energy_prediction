# docs/api-contracts.md — Diagonally Energy Prediction

## POST /api/v1/predict/full

Smart Home tier. Accepts all 25 sensor + weather features. Weather is fetched
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

## GET /health

**Response — 200:**
```json
{ "status": "ok" }
```
