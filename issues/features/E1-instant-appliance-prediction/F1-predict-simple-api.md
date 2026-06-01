---
epic: E1-instant-appliance-prediction
feature: F1
slug: predict-simple-api
---

# F1 — POST /api/v1/predict/simple API

## Goal

The prediction endpoint exists, is tested, and returns correct results. Given
lights (Wh), T1 (°C), and a city name, the API fetches outside weather
automatically, assembles 7 features, runs model_simple.joblib, calculates the
NGN cost, stores the result in Supabase, and returns a JSON response — all
within 2 seconds.

## User Story

As a developer integrating the Basic tier, I want a tested API endpoint at
POST /api/v1/predict/simple so that any client can submit three values and
receive a complete prediction response without knowing anything about the model
or weather data.

## Issues

1. **Train and save model_simple.joblib** — Run scripts/run_training_simple.py
   to train all six regression models on the 7-feature set (lights, T1, T_out,
   RH_out, Windspeed, Visibility, Tdewpoint). Evaluate R² on held-out test
   split. Save the best model to src/model/trained/model_simple.joblib.

2. **Implement weather.py** — Fetch T_out, RH_out, Windspeed, Visibility,
   Tdewpoint from OpenWeatherMap Current Weather API by city name. Cache
   responses for 10 minutes using cachetools TTLCache keyed by city name.
   Raise HTTPException 500 if the fetch fails.

3. **Implement POST /api/v1/predict/simple** — Accept `lights`, `T1`,
   `location` via Pydantic model. Call weather.py for outside features.
   Assemble 7-feature dict. Load model_simple singleton and run inference.
   Call cost.py to convert Wh → kWh → NGN. Insert row into Supabase
   predictions table. Return `predicted_wh`, `predicted_kwh`,
   `estimated_cost_ngn`, `weather_factors`.

4. **Write tests** — test_api.py: valid input returns 200 with correct fields;
   missing field returns 422; unknown city returns 500. test_weather.py: second
   call within 10 minutes does not make a second HTTP request.

## Out of Scope

- Frontend form or result display
- model_full or the full tier endpoint
- Prediction history endpoint
- Forecast endpoints
