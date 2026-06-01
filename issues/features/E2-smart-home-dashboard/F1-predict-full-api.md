---
epic: E2-smart-home-dashboard
feature: F1
slug: predict-full-api
---

# F1 — POST /api/v1/predict/full API

## Goal

The Smart Home prediction endpoint exists, is tested, and returns correct
results. Given 19 sensor fields (T1–T9, RH_1–RH_9, lights) and a location, the
API fetches 6 outside weather features automatically, assembles a 25-feature
dict, runs model_full.joblib, calculates the NGN cost, stores the result in
Supabase, and returns predicted_wh, predicted_kwh, and estimated_cost_ngn —
within 2 seconds.

## User Story

As a developer integrating the Smart Home tier, I want a tested API endpoint at
POST /api/v1/predict/full so that the scheduler and any other client can submit
sensor readings and receive a complete prediction response without needing to
know anything about the model or weather enrichment.

## Issues

1. **Train and save model_full.joblib** — Run scripts/run_training_full.py to
   train all six regression models (Random Forest, XGBoost, LightGBM, CatBoost,
   Extra Trees, Ridge) on the 25-feature set. Evaluate R² on held-out test
   split. Save the best model to src/model/trained/model_full.joblib.

2. **Implement POST /api/v1/predict/full route** — Accept 19 sensor fields +
   location via Pydantic model. Call weather.py (built in E1/F1) to fetch the
   6 outside features. Assemble 25-feature dict in the order defined in
   CLAUDE.md ML conventions. Load model_full singleton and run inference.
   Call cost.py to convert Wh → kWh → NGN. Insert row into Supabase
   predictions table with tier='full'. Return predicted_wh, predicted_kwh,
   estimated_cost_ngn.

3. **Write tests** — test_api.py: valid 19-field body returns 200 with all
   three response fields; missing sensor field returns 422; weather fetch
   failure returns 500. Confirm Supabase insert is called once per request.

## Out of Scope

- APScheduler or automatic submission (F2)
- Dashboard frontend (F3)
- History chart and table (F4)
- model_simple or the Basic tier endpoint
