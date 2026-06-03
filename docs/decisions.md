# docs/decisions.md — Diagonally Energy Prediction

## ADR-002: Three time series models evaluated for forecast
Chronos-Bolt (Small), MSTL, and XGBoost with lag features all trained and
evaluated. Best MAPE on held-out test split saved as model_forecast.joblib.
Chronos-Bolt is a zero-shot pre-trained transformer from Amazon — no fine-tuning
required, strong out-of-the-box on household energy data.

## ADR-003: MSTL via statsforecast
statsforecast's MSTL (Multiple Seasonal-Trend decomposition using LOESS) handles
the daily (6 × 10-min = 1-hour, 144 × 10-min = 24-hour) seasonalities present
in household energy data. Lightweight and interpretable.

## ADR-005: Unix column dropped at preprocessing
The Unix timestamp is converted to a UK-local datetime index during loading;
the raw integer column is then discarded.

## ADR-006: REFIT Smart Home Dataset — House 1
Covers Oct 9 2013 – Jan 2 2014 with 8-second readings for 9 individual
appliances. Chosen over UCI Appliances Energy because it provides per-appliance
granularity (Fridge, Freezers, Washing Machine, etc.) and is a UK household,
consistent with GBP tariff.

## ADR-007: Confidence intervals for bill projection
Monthly bill returned as optimistic (yhat_lower), most likely (yhat) and
pessimistic (yhat_upper). Homeowners get a realistic range rather than a
single number.

## ADR-008: APScheduler replays test split rows
Scheduler iterates chronologically through test.csv (Dec 16 – Jan 2) instead of
reading live sensors. This gives a deterministic, reproducible demo without
requiring real Zigbee hardware. predicted_wh is taken directly from the
aggregate_wh column — no model inference on the scheduler tick.

## ADR-009: joblib for forecast model persistence
Standard for scikit-learn-compatible models. Fast load of numpy arrays.
model_forecast.joblib is loaded once at startup as a singleton — never
reloaded per request.

## ADR-010: UK electricity tariff in environment variable
Rate can change without a redeploy (Ofgem revises quarterly). Applied to
predicted kWh for both current prediction and monthly bill projection.

## ADR-012: Chronological train/test split — no shuffle
Train: Oct 9 – Dec 15 2013 (67 days). Test: Dec 16 – Jan 2 2014 (18 days).
Shuffling would leak future data into training — never allowed for time series.

## ADR-013: Retraining uses MAPE comparison for forecast model
When retraining is triggered, the new forecast model is only deployed if its
MAPE on the held-out test split is strictly lower than the current model's MAPE
(recorded in forecast_leaderboard.json). Lower MAPE = better forecast accuracy.
