# docs/decisions.md â€” Diagonally Energy Prediction
<!-- TODO: Fill after running /write-specs -->

## ADR-001: Random Forest as baseline model
Random Forest chosen as the first model for its robustness to outliers,
no need for feature scaling, and strong performance on tabular time series.
XGBoost to be evaluated in a later sprint.

## ADR-002: joblib for model persistence
joblib is the standard for scikit-learn model serialization.
Smaller file size and faster load than pickle for numpy arrays.

## ADR-003: Features engineered offline, not in API
Feature engineering runs at training time and produces features.csv.
The API receives already-engineered features to keep inference fast and simple.
