---
epic: E3-energy-forecast-and-bill-projection
feature: F1
slug: forecast-24h-api
---

# F1 — GET /api/v1/forecast/24h API

## Goal

The 24-hour forecast endpoint exists and is tested. Given a city name, the API
runs model_forecast.joblib to produce an hourly forecast for the next 24 hours
with confidence intervals, applies the NERC tariff to each hour, and returns
a JSON array plus peak_hour and lowest_hour callouts — all within 2 seconds.

## User Story

As a developer building the forecast page, I want a tested API endpoint at
GET /api/v1/forecast/24h that accepts a location and returns hourly predicted
consumption with confidence bounds and NGN cost per hour, so the frontend can
render a chart without doing any model work itself.

## Issues

1. **Train all 5 time series models and save the best as model_forecast.joblib**
   — Run scripts/run_training_forecast.py. Train Prophet, XGBoost with lag
   features (lag_1h, lag_24h, lag_168h, rolling_mean_3h, rolling_mean_24h),
   LightGBM with same lags, LSTM (via neuralforecast), and TFT (via
   neuralforecast). Evaluate MAPE on held-out test split. Save the best MAPE
   model to src/model/trained/model_forecast.joblib.

2. **Implement forecast.py** — Load model_forecast.joblib once at startup as a
   singleton. Expose a `forecast_24h(location: str) -> list[dict]` function
   that calls weather.py for current outside conditions, generates 24 hourly
   predictions with yhat, yhat_lower, yhat_upper. Return list of dicts with
   fields: ds, yhat, yhat_lower, yhat_upper, predicted_kwh, estimated_cost_ngn.

3. **Implement GET /api/v1/forecast/24h route** — Accept `location` as a query
   param. Call forecast.py. Compute peak_hour (highest yhat) and lowest_hour
   (lowest yhat) from the returned array. Return the full forecast array plus
   peak_hour and lowest_hour.

4. **Write tests** — test_api.py: valid location returns 200 with a 24-element
   array; each element contains all required fields; peak_hour is the ds value
   with the highest yhat; unknown location returns 500.

## Out of Scope

- 7-day forecast (F2)
- Monthly bill projection (F2)
- forecast.html frontend (F3)
- Model leaderboard endpoint (F4)
