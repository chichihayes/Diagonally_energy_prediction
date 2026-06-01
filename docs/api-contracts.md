# docs/api-contracts.md â€” Diagonally Energy Prediction
<!-- TODO: Fill after running /write-specs -->

## POST /api/v1/predict
Request:
```json
{
  "hour": 14,
  "day_of_week": 2,
  "month": 6,
  "is_weekend": 0,
  "lag_1h": 0.45,
  "lag_24h": 0.50,
  "lag_168h": 0.48,
  "rolling_mean_3h": 0.47,
  "rolling_mean_24h": 0.49
}
```
Response:
```json
{
  "predicted_kwh": 0.512
}
```

## GET /health
Response:
```json
{ "status": "ok" }
```
