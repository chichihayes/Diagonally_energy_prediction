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
Covers Oct 9 2013 – Jul 10 2015 (638 days) with 8-second readings for 9 individual
appliances. There is a 41-day sensor gap in March–April 2014; rows in that window
are dropped naturally by dropna() on the lag_1008 feature. Chosen over UCI Appliances
Energy because it provides per-appliance granularity (Fridge, Freezers, Washing
Machine, etc.) and is a UK household, consistent with GBP tariff.

## ADR-007: Confidence intervals for bill projection
Monthly bill returned as optimistic (yhat_lower), most likely (yhat) and
pessimistic (yhat_upper). Homeowners get a realistic range rather than a
single number.

## ADR-008: APScheduler replays test split rows
Scheduler iterates chronologically through test.csv (Dec 29 2014 – Jul 10 2015) instead of
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
Train: Oct 16 2013 – Dec 28 2014 (~14 months, 56,198 rows, 70%). Test: Dec 29 2014 – Jul 10 2015
(~7 months, 23,924 rows, 30%). Split date is _TRAIN_END = "2014-12-28" in data_loader.py.
Shuffling would leak future data into training — never allowed for time series.

## ADR-011: Regression model layer removed — forecast-only architecture
The original design had two regression model layers (full: 25 features, simple: 7 features)
that predicted aggregate Wh from live sensor inputs via POST /predict/full and POST /predict/simple.
These were removed in the REFIT migration because: (1) the REFIT dataset has no live sensor
inputs — it is appliance-level Wh readings, not room temperature/humidity; (2) the
scheduler-replay architecture means no live inference path is needed; (3) only the time
series forecast model (Chronos-Bolt/MSTL/XGBoost) is needed for the 24h and 7d forecast
endpoints. The retraining pipeline was repurposed to retrain only the forecast model.

## ADR-014: IQR outlier capping removed from preprocessing
`_cap_outliers_iqr` was removed from `preprocess()` in `data_loader.py`. When more
than 75% of 10-minute resampled values are zero (TumbleDryer, WashingMachine,
Dishwasher, Computer, Television), Q1=Q3=0, IQR=0, and clip([0,0]) silently
destroys all real readings. The three forecast models (Chronos-Bolt, MSTL, XGBoost)
are robust to outliers and train on aggregate_wh — IQR capping offers no benefit
and introduces significant bias for sparse appliances. `clip(lower=0)` is retained
to remove unphysical negative sensor readings.

## ADR-013: Retraining uses MAPE comparison for forecast model
When retraining is triggered, the new forecast model is only deployed if its
MAPE on the held-out test split is strictly lower than the current model's MAPE
(recorded in forecast_leaderboard.json). Lower MAPE = better forecast accuracy.
