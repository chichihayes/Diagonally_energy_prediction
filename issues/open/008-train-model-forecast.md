---
id: "008"
slug: train-model-forecast
feature: F1
epic: E3
title: Train all 5 time series models and save the best as model_forecast.joblib
status: open
---

# 008 — Train all 5 time series models and save the best as model_forecast.joblib

## Goal

A trained time series model exists at `src/model/trained/model_forecast.joblib` so
the `/api/v1/forecast/24h` endpoint has a model to load at startup and serve
24-hour predictions without retraining on every request.

## User Story

As a developer building the forecast endpoint, I want a pretrained model at
`src/model/trained/model_forecast.joblib` so the server can load it once at
startup and return hourly predictions for the next 24 hours without any
retraining happening inside the API process.

## Reference Docs

- `docs/schema.md` — forecast output schema, lag feature definitions
- `docs/architecture.md` — training data flow, evaluate.py role, scripts/ as offline entrypoint
- `CLAUDE.md` — ML conventions: MAPE metric, 5 time series models, lag feature list, joblib persistence

## Acceptance Criteria

- [ ] `scripts/run_training_forecast.py` executes without error when `data/raw/KAG_energydata_complete.csv` is present
- [ ] Running the script produces `src/model/trained/model_forecast.joblib`
- [ ] `build_lag_matrix(df)` in `features.py` returns a DataFrame with exactly these columns: `lag_1h, lag_24h, lag_168h, rolling_mean_3h, rolling_mean_24h`, plus target series — no NaNs after dropna
- [ ] `select_best_by_mape(candidates)` in `evaluate.py` returns the tuple with the lowest MAPE value
- [ ] All 5 models are trained: Prophet, XGBoost with lags, LightGBM with lags, LSTM (via neuralforecast), TFT (via neuralforecast)
- [ ] Best MAPE model is saved as `model_forecast.joblib` via joblib
- [ ] Loaded model produces output that includes `yhat`, `yhat_lower`, `yhat_upper` for 24 hourly steps

## Files to Modify

- `src/services/features.py` — add `build_lag_matrix(df)`
- `src/model/evaluate.py` — add `select_best_by_mape(candidates)`
- `src/model/train_forecast.py` — create (train 5 time series models, evaluate MAPE, save best)
- `scripts/run_training_forecast.py` — create (offline entrypoint)

> `data_loader.py` and `evaluate.py` already exist. Only add `select_best_by_mape` — do not modify existing functions.

## Out of Scope

- Loading the model into `forecast.py` (issue 009)
- The API route handler (issue 010)
- API-level tests (issue 011)
- 7-day forecast training (F2)

## Implementation Plan

### Step 1 — features.py: add `build_lag_matrix(df)`

The dataset is sampled every 10 minutes, so:
- `lag_1h` = 6 steps back
- `lag_24h` = 144 steps back
- `lag_168h` = 1008 steps back (1 week)
- `rolling_mean_3h` = rolling window of 18 steps (shifted by 1 to avoid leakage)
- `rolling_mean_24h` = rolling window of 144 steps (shifted by 1 to avoid leakage)

**Test** (`tests/test_features.py`):
```python
def test_build_lag_matrix_returns_correct_columns():
    from src.services.data_loader import load_and_split
    from src.services.features import build_lag_matrix
    train, _ = load_and_split()
    X, y = build_lag_matrix(train)
    expected = ["lag_1h", "lag_24h", "lag_168h", "rolling_mean_3h", "rolling_mean_24h"]
    assert list(X.columns) == expected
    assert y.name == "Appliances"

def test_build_lag_matrix_has_no_nulls_after_dropna():
    from src.services.data_loader import load_and_split
    from src.services.features import build_lag_matrix
    train, _ = load_and_split()
    X, y = build_lag_matrix(train)
    assert X.isna().sum().sum() == 0
    assert y.isna().sum() == 0
```

**File:** `src/services/features.py` — add:

```python
def build_lag_matrix(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    series = df["Appliances"].copy()
    lags = pd.DataFrame({
        "lag_1h": series.shift(6),
        "lag_24h": series.shift(144),
        "lag_168h": series.shift(1008),
        "rolling_mean_3h": series.shift(1).rolling(18).mean(),
        "rolling_mean_24h": series.shift(1).rolling(144).mean(),
    }, index=df.index)
    combined = lags.join(series).dropna()
    return combined.drop("Appliances", axis=1), combined["Appliances"]
```

---

### Step 2 — evaluate.py: add `select_best_by_mape(candidates)`

`candidates` is a list of `(name: str, model: any, mape: float)` tuples. Lower MAPE is better.

**Test** (`tests/test_evaluate.py`):
```python
def test_select_best_by_mape_returns_lowest_mape():
    from src.model.evaluate import select_best_by_mape
    candidates = [
        ("Prophet", "model_a", 12.5),
        ("LightGBM_lags", "model_b", 8.1),
        ("XGBoost_lags", "model_c", 10.0),
    ]
    name, model, mape = select_best_by_mape(candidates)
    assert name == "LightGBM_lags"
    assert model == "model_b"
    assert mape == 8.1

def test_select_best_by_mape_single_candidate():
    from src.model.evaluate import select_best_by_mape
    candidates = [("Prophet", "only_model", 15.0)]
    name, model, mape = select_best_by_mape(candidates)
    assert name == "Prophet"
```

**File:** `src/model/evaluate.py` — add:

```python
def select_best_by_mape(candidates: list[tuple]) -> tuple:
    return min(candidates, key=lambda c: c[2])
```

---

### Step 3 — train_forecast.py: train 5 models, evaluate MAPE, save best

Prophet requires a DataFrame with `ds` (datetime) and `y` (float) columns.
XGBoost/LightGBM use `build_lag_matrix` output.
LSTM and TFT use neuralforecast with the Appliances series and a datetime index.

Each model must produce a predict interface returning `yhat`, `yhat_lower`, `yhat_upper`
for 24 future hourly steps. Save the best model together with its type string so
`forecast.py` can dispatch the correct inference path:

```python
joblib.dump({"model": best_model, "model_type": best_name}, output_path)
```

**Test** (`tests/test_model.py`):
```python
def test_train_forecast_produces_loadable_model(tmp_path):
    import joblib
    from src.model.train_forecast import train_and_save
    out = tmp_path / "model_forecast.joblib"
    train_and_save(output_path=str(out))
    assert out.exists()
    artifact = joblib.load(str(out))
    assert "model" in artifact
    assert "model_type" in artifact
    assert artifact["model_type"] in {
        "Prophet", "XGBoost_lags", "LightGBM_lags", "LSTM", "TFT"
    }
```

**File:** `src/model/train_forecast.py` — create.

---

### Step 4 — scripts/run_training_forecast.py: thin offline entrypoint

No test needed — single delegating call.

**File:** `scripts/run_training_forecast.py`

```python
from src.model.train_forecast import train_and_save
train_and_save()
print("model_forecast.joblib saved.")
```

## Git

- **Branch:** `feat/008-train-model-forecast`
- **Commit format:** `feat(model): train 5 time series models on Appliances series, save best MAPE as model_forecast.joblib`
- **PR title:** `feat(model): train and save model_forecast.joblib`
