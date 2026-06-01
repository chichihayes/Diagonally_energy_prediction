---
id: "001"
slug: train-model-simple
feature: F1
epic: E1
title: Train and save model_simple.joblib
status: open
---

# 001 — Train and save model_simple.joblib

## Goal

A trained regression model exists at `src/model/trained/model_simple.joblib` so
the `/api/v1/predict/simple` endpoint has a model to load at startup.

## User Story

As a developer running the Basic tier API, I want a pretrained model at
`src/model/trained/model_simple.joblib` so the server can load it once at startup
and serve predictions without retraining.

## Reference Docs

- `docs/schema.md` — model_simple feature set (7 features)
- `docs/architecture.md` — training data flow, evaluate.py role, scripts/ as offline entrypoint
- `CLAUDE.md` — ML conventions: 80/20 time-ordered split, R² metric, best-model selection, joblib persistence

## Acceptance Criteria

- [ ] `scripts/run_training_simple.py` executes without error when `data/raw/KAG_energydata_complete.csv` is present
- [ ] Running the script produces `src/model/trained/model_simple.joblib`
- [ ] `evaluate.py` receives scores for all six models (RF, XGBoost, LightGBM, CatBoost, ExtraTrees, Ridge) and returns the one with the highest R²
- [ ] Saved model accepts a dict of 7 features and returns a float without error
- [ ] `rv1` and `rv2` are never present in any training array passed to any model
- [ ] Train/test split is 80/20, time-ordered (no shuffle)
- [ ] `src/model/trained/model_simple.joblib` can be loaded with `joblib.load()` and called with `.predict()`

## Files to Modify

- `src/model/train_simple.py` — create (train 6 models on 7-feature set, call evaluate, save best)
- `src/model/evaluate.py` — create (accept list of `(name, model, r2)` tuples, return winner)
- `src/services/data_loader.py` — create (load CSV, drop `date`/`rv1`/`rv2`, split 80/20 time-ordered)
- `src/services/features.py` — create `build_simple_matrix(df)` (select 7 columns from preprocessed df)
- `scripts/run_training_simple.py` — create (offline entrypoint: call `train_simple.train_and_save()`)

## Out of Scope

- Training `model_full.joblib` or `model_forecast.joblib`
- Any API route or request handling
- Supabase reads or writes
- Weather API calls

## Implementation Plan

### Step 1 — data_loader: load CSV and split

**Test** (`tests/test_model.py`):
```python
def test_data_loader_returns_train_test_split():
    from src.services.data_loader import load_and_split
    train, test = load_and_split()
    assert len(train) + len(test) == 19735
    assert len(train) == pytest.approx(19735 * 0.8, abs=5)
    assert "rv1" not in train.columns
    assert "rv2" not in train.columns
    assert "date" not in train.columns
    assert "Appliances" in train.columns
```

**File:** `src/services/data_loader.py`

Implement `load_and_split() -> tuple[pd.DataFrame, pd.DataFrame]`:
- Read `data/raw/KAG_energydata_complete.csv`
- Drop `date`, `rv1`, `rv2`
- Split at index `int(len(df) * 0.8)` — no shuffle
- Return `(train_df, test_df)`

---

### Step 2 — features: build simple matrix

**Test** (`tests/test_features.py`):
```python
def test_build_simple_matrix_returns_7_columns():
    from src.services.data_loader import load_and_split
    from src.services.features import build_simple_matrix
    train, _ = load_and_split()
    X, y = build_simple_matrix(train)
    assert list(X.columns) == ["lights", "T1", "T_out", "RH_out", "Windspeed", "Visibility", "Tdewpoint"]
    assert y.name == "Appliances"
    assert len(X) == len(y)
```

**File:** `src/services/features.py`

Implement `build_simple_matrix(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]`:
- Select columns `["lights", "T1", "T_out", "RH_out", "Windspeed", "Visibility", "Tdewpoint"]`
- Return `(X, y)` where `y = df["Appliances"]`

---

### Step 3 — evaluate: pick best model by R²

**Test** (`tests/test_evaluate.py`):
```python
def test_evaluate_returns_highest_r2_model():
    from src.model.evaluate import select_best_by_r2
    import numpy as np
    dummy = lambda: None
    candidates = [("RF", dummy, 0.80), ("XGB", dummy, 0.91), ("Ridge", dummy, 0.70)]
    name, model, score = select_best_by_r2(candidates)
    assert name == "XGB"
    assert score == 0.91

def test_evaluate_rejects_empty_list():
    from src.model.evaluate import select_best_by_r2
    with pytest.raises(ValueError):
        select_best_by_r2([])
```

**File:** `src/model/evaluate.py`

Implement `select_best_by_r2(candidates: list[tuple[str, Any, float]]) -> tuple[str, Any, float]`:
- Raise `ValueError` if `candidates` is empty
- Return the tuple with the highest R² score

---

### Step 4 — train_simple: train 6 models, save best

**Test** (`tests/test_model.py`):
```python
def test_train_simple_produces_loadable_model(tmp_path):
    import joblib, os
    from src.model.train_simple import train_and_save
    out = tmp_path / "model_simple.joblib"
    train_and_save(output_path=str(out))
    assert out.exists()
    model = joblib.load(str(out))
    import pandas as pd
    sample = pd.DataFrame([{
        "lights": 0, "T1": 20.0, "T_out": 28.0,
        "RH_out": 80.0, "Windspeed": 3.0, "Visibility": 10.0, "Tdewpoint": 25.0
    }])
    result = model.predict(sample)
    assert isinstance(float(result[0]), float)
```

**File:** `src/model/train_simple.py`

Implement `train_and_save(output_path: str = "src/model/trained/model_simple.joblib")`:
- Call `load_and_split()` → `train_df`, `test_df`
- Call `build_simple_matrix(train_df)` → `X_train`, `y_train`
- Call `build_simple_matrix(test_df)` → `X_test`, `y_test`
- Fit all six models: `RandomForestRegressor`, `XGBRegressor`, `LGBMRegressor`, `CatBoostRegressor(verbose=0)`, `ExtraTreesRegressor`, `Ridge`
- Evaluate each with `r2_score(y_test, model.predict(X_test))`
- Call `select_best_by_r2(candidates)` → winner
- `joblib.dump(winner_model, output_path)`

---

### Step 5 — script: offline entrypoint

**File:** `scripts/run_training_simple.py`

```python
from src.model.train_simple import train_and_save
train_and_save()
print("model_simple.joblib saved.")
```

No test required — this is a thin shell script delegating to `train_and_save`.

## Git

- **Branch:** `feat/001-train-model-simple`
- **Commit format:** `feat(model): train 6 regression models on 7 features, save best R² as model_simple.joblib`
- **PR title:** `feat(model): train and save model_simple.joblib`
