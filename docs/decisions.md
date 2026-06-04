# docs/decisions.md — Diagonally Energy Prediction

## ADR-002: RandomForest with temperature features for forecast
RandomForest (300 trees, depth 10) trained on 11 features: 9 lag/calendar features
(day_of_week, month, is_weekend, lag_1, lag_7, rolling_mean_7, heater_lag_1,
heater_lag_7, heater_rolling_mean_7) plus temp_mean_c and temp_min_c from
Open-Meteo historical archive. Achieves 16.6% MAPE on 9 strategic test days.
Chosen over Chronos-Bolt/MSTL/Prophet after multi-model notebook comparison:
more accurate, no heavy dependencies, fast training (< 30 s).

## ADR-003: 9 strategic test days instead of walk-forward evaluation
The 9 test dates (3 LOW / 3 MID / 3 HIGH, spread across the full date range)
were hand-picked to cover seasonal variation and consumption tiers. Walk-forward
evaluation was dropped because: (1) it requires many more model fits per evaluation,
(2) the strategic test days gave a cleaner signal on generalisation, (3) single-step
point evaluation is sufficient for a 7-day forecast use case.

## ADR-005: Unix column dropped at preprocessing
The Unix timestamp is converted to a UK-local datetime index during loading;
the raw integer column is then discarded.

## ADR-006: REFIT Smart Home Dataset — House 1
Covers Oct 9 2013 – Jul 10 2015 (638 days) with 8-second readings for 9 individual
appliances. There is a 41-day sensor gap in March–April 2014; rows in that window
are dropped naturally by dropna() on lag features. Chosen over UCI Appliances
Energy because it provides per-appliance granularity (Fridge, Freezers, Washing
Machine, etc.) and is a UK household, consistent with GBP tariff.

## ADR-007: Weekly bill projection with confidence interval
Weekly bill returned as optimistic (lower_wh), most likely (predicted_wh) and
pessimistic (upper_wh). Confidence interval is ±15% of predicted_wh — a simple
fixed band rather than model-derived uncertainty. Homeowners get a realistic
range rather than a single number.

## ADR-009: joblib for forecast model persistence
Standard for scikit-learn-compatible models. Fast load of numpy arrays.
model_forecast.joblib is loaded once at startup as a singleton in forecast.py —
never reloaded per request. The model is wrapped in _TreeWrapper to provide a
uniform predict() and predict_from_features() interface.

## ADR-010: UK electricity tariff in environment variable
Rate can change without a redeploy (Ofgem revises quarterly). Applied to
predicted kWh for both single-day prediction and weekly bill projection.
Variable: ELECTRICITY_TARIFF_GBP_PER_KWH. Current rate: 0.34 GBP/kWh.

## ADR-011: Regression model layer removed — forecast-only architecture
The original design had two regression model layers (full: 25 features, simple: 7 features)
that predicted aggregate Wh from live sensor inputs via POST /predict/full and POST /predict/simple.
These were removed in the REFIT migration because: (1) the REFIT dataset has no live sensor
inputs — it is appliance-level Wh readings, not room temperature/humidity; (2) only the time
series forecast model is needed for the 24h and 7d forecast endpoints.

## ADR-014: IQR outlier capping removed from preprocessing
`_cap_outliers_iqr` was removed from `preprocess()` in `data_loader.py`. When more
than 75% of 10-minute resampled values are zero (TumbleDryer, WashingMachine,
Dishwasher, Computer, Television), Q1=Q3=0, IQR=0, and clip([0,0]) silently
destroys all real readings. RandomForest is robust to outliers and trains on
aggregate_wh — IQR capping offers no benefit and introduces significant bias for
sparse appliances. `clip(lower=0)` is retained to remove unphysical negative
sensor readings.

## ADR-015: training_stats.json removed — appliance fractions and day-of-week means dropped
`training_stats.json` previously stored `appliance_fractions` and `daily_mean_by_dow`
to enrich forecast responses with per-appliance breakdowns and a HIGH/LOW/NORMAL flag.
These were removed because: (1) the frontend never used them; (2) the fields
(`appliance_contribution`, `is_unusual`, `pct_vs_normal`) were decorative and added
no value to the prediction; (3) the file added a training-time artefact with no
corresponding test coverage benefit. The model prediction (predicted_wh, predicted_kwh,
estimated_cost_gbp) is unchanged.

## ADR-016: Temperature fields added as optional POST inputs
`temp_mean_c` and `temp_min_c` are optional on POST /api/v1/forecast/predict.
If supplied, they are used directly; if omitted, the backend fetches them from
Open-Meteo. This allows the frontend to show all 11 model features explicitly
and lets users override temperature for what-if scenarios without changing the backend
model or adding a separate endpoint.
