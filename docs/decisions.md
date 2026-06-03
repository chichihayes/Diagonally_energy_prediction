# docs/decisions.md — Diagonally Energy Prediction

## ADR-001: Six regression models evaluated for Layer 1
Random Forest, XGBoost, LightGBM, CatBoost, Extra Trees and Ridge Regression
all trained and evaluated on the same feature set (time features + lag features).
Best R² on held-out test split saved as final model.

## ADR-002: Three time series models evaluated for Layer 2
Chronos-Bolt (Small), MSTL, and XGBoost with lag features all trained and
evaluated. Best MAPE on held-out test split saved as model_forecast.joblib.
Chronos-Bolt is a zero-shot pre-trained transformer from Amazon — no fine-tuning
required, strong out-of-the-box on household energy data.

## ADR-003: MSTL via statsforecast
statsforecast's MSTL (Multiple Seasonal-Trend decomposition using LOESS) handles
the daily (6 × 10-min = 1-hour, 144 × 10-min = 24-hour) seasonalities present
in household energy data. Lightweight and interpretable.

## ADR-004: Single regression model (full tier only)
REFIT data has no room temperature or humidity sensors — the feature set is
purely time-based and lag-based. There is no "simple" vs "full" tier distinction.
model_full.joblib is trained on all 13 MODEL_FEATURES.

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
requiring real Zigbee hardware.

## ADR-009: joblib for all model persistence
Standard for scikit-learn models. Fast load of numpy arrays. Models loaded once
at startup as singletons — never reloaded per request.

## ADR-010: UK electricity tariff in environment variable
Rate can change without a redeploy (Ofgem revises quarterly). Applied to
predicted kWh for both current prediction and monthly bill projection.

## ADR-011: StandardScaler saved as artifact
Scaler fitted on train split features only, saved as scaler.joblib. Applied to
features at training time and at inference time (scheduler). Drift detection
compares unscaled features against unscaled training_stats.json.

## ADR-012: Chronological train/test split — no shuffle
Train: Oct 9 – Dec 15 2013 (67 days). Test: Dec 16 – Jan 2 2014 (18 days).
Shuffling would leak future data into training — never allowed for time series.
