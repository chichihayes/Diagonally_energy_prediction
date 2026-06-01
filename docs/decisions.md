# docs/decisions.md â€” Diagonally Energy Prediction
<!-- TODO: Fill after running /write-specs -->

## ADR-001: Random Forest as baseline model
Random Forest chosen for its robustness to multicollinearity across 28 correlated temperature and humidity features, no need for feature scaling, and strong performance on tabular data.

## ADR-002: joblib for model persistence
Standard for scikit-learn, fast load time for numpy arrays.

## ADR-003: rv1 and rv2 dropped at preprocessing
These are random noise variables included by the dataset authors to test model robustness. They have no predictive value.

## ADR-004: lights feature kept separate from Appliances
lights energy is a raw sensor reading, not part of the Appliances target, so it is an input feature not a label.
