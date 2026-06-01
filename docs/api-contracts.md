# docs/api-contracts.md â€” Diagonally Energy Prediction
<!-- TODO: Fill after running /write-specs -->

## POST /api/v1/predict
Request:
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
  "T_out": 6.6,
  "Press_mm_hg": 733.5,
  "RH_out": 92.0,
  "Windspeed": 7.0,
  "Visibility": 63.0,
  "Tdewpoint": 5.3
}
```
Response:
```json
{
  "predicted_wh": 60.5
}
```

## GET /health
Response:
```json
{ "status": "ok" }
```
