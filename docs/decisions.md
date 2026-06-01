# docs/decisions.md — Diagonally Energy Prediction

## ADR-001: Six regression models evaluated for Layer 1
Random Forest, XGBoost, LightGBM, CatBoost, Extra Trees and Ridge Regression 
all trained and evaluated on same feature sets. Best R² on held-out test split 
saved as final model. This approach ensures we pick the objectively best model 
rather than assuming one will win.

## ADR-002: Five time series models evaluated for Layer 2
Prophet, XGBoost with lag features, LightGBM with lag features, LSTM and TFT 
(Temporal Fusion Transformer) all trained and evaluated. Best MAPE on held-out 
test split saved as model_forecast.joblib. TFT is state of the art for time 
series — included to maximise forecast accuracy.

## ADR-003: TFT and LSTM via neuralforecast library
neuralforecast provides a unified scikit-learn style API for neural time series 
models including TFT and LSTM. Chosen over raw PyTorch to reduce boilerplate 
and keep training code consistent across all five forecast models.

## ADR-004: Two separate regression models saved
model_full.joblib trained on 26 features for Smart Home tier.
model_simple.joblib trained on 7 features for Basic tier.
Basic tier users have no sensors — simpler model gives meaningful predictions 
without requiring all 26 inputs.

## ADR-005: rv1 and rv2 dropped at preprocessing
Random noise variables added by dataset authors to test model robustness. 
No predictive value — confirmed by feature importance across all models.

## ADR-006: OpenWeatherMap free tier for outside weather
Supplies T_out, RH_out, Windspeed, Visibility, Tdewpoint, Press_mm_hg 
automatically. Responses cached 10 minutes to keep predictions under 2 seconds 
and stay within free tier rate limits.

## ADR-007: Prophet confidence intervals for bill projection
Monthly bill returned as optimistic (yhat_lower), most likely (yhat) and 
pessimistic (yhat_upper) range. Homeowners get a realistic picture rather than 
a single number that may mislead them.

## ADR-008: APScheduler runs inside FastAPI process
Chosen over a separate cron job or Celery worker to keep deployment simple for 
the demo. Submits Smart Home readings every 15 minutes automatically on startup.

## ADR-009: joblib for all model persistence
Standard for scikit-learn models. Fast load of numpy arrays. All three models 
loaded once at startup as singletons — never reloaded per request.

## ADR-010: NERC tariff rate in environment variable
Rate can change without a redeploy. Applied to predicted kWh for both current 
prediction and monthly bill projection.
