---
id: "005"
slug: train-model-full
feature: F1
epic: E2
title: Train and save model_full.joblib
status: open
---

# 005 — Train and save model_full.joblib

## Goal

A trained regression model exists at `src/model/trained/model_full.joblib` so
the `/api/v1/predict/full` endpoint has a 25-feature model to load at startup.

## User Story

As a developer running the Smart Home tier API, I want a pretrained model at
`src/model/trained/model_full.joblib` so the server can load it once at startup
and serve accurate predictions from all 25 sensor and weather features without
retraining.

## Reference Docs

- `docs/schema.md` — model_full 25-feature list and column order
- `docs/architecture.md` — training data flow, evaluate.py role, scripts/ as offline entrypoint
- `CLAUDE.md` — ML conventions: 80/20 time-ordered split, R² metric, best-model selection, joblib persistence

## Acceptance Criteria

- [ ] `scripts/run_training_full.py` executes without error when `data/raw/KAG_energydata_complete.csv` is present
- [ ] Running the script produces `src/model/trained/model_full.joblib`
- [ ] `build_full_matrix(df)` returns exactly 25 columns in the order defined in `docs/schema.md`: `lights, T1, RH_1, T2, RH_2, T3, RH_3, T4, RH_4, T5, RH_5, T6, RH_6, T7, RH_7, T8, RH_8, T9, RH_9, T_out, Press_mm_hg, RH_out, Windspeed, Visibility, Tdewpoint`
- [ ] `rv1` and `rv2` are never present in any training array
- [ ] All six models (RF, XGBoost, LightGBM, CatBoost, ExtraTrees, Ridge) are evaluated — winner is the highest R²
- [ ] Train/test split is 80/20, time-ordered (no shuffle)
- [ ] Saved model accepts a dict of 25 features and returns a float without error

## Files to Modify

- `src/services/features.py` — add `build_full_matrix(df)` (select 25 columns from preprocessed df)
- `src/model/train_full.py` — create (train 6 models on 25-feature set, call `select_best_by_r2`, save best)
- `scripts/run_training_full.py` — create (offline entrypoint: call `train_full.train_and_save()`)

> `data_loader.py` and `evaluate.py` already exist from issue 001. Do not modify them.

## Out of Scope

- Training `model_simple.joblib` or `model_forecast.joblib`
- Any API route or request handling
- Supabase reads or writes
- Weather API calls
- Adding `build_full_matrix` to inference path (that is issue 006)

## Implementation Plan

### Step 1 — features.py: build full matrix (25 columns)

**Test** (`tests/test_features.py`):
```python
def test_build_full_matrix_returns_25_columns():
    from src.services.data_loader import load_and_split
    from src.services.features import build_full_matrix
    train, _ = load_and_split()
    X, y = build_full_matrix(train)
    expected_cols = [
        "lights", "T1", "RH_1", "T2", "RH_2", "T3", "RH_3", "T4", "RH_4",
        "T5", "RH_5", "T6", "RH_6", "T7", "RH_7", "T8", "RH_8", "T9", "RH_9",
        "T_out", "Press_mm_hg", "RH_out", "Windspeed", "Visibility", "Tdewpoint",
    ]
    assert list(X.columns) == expected_cols
    assert y.name == "Appliances"
    assert len(X) == len(y)

def test_build_full_matrix_excludes_rv_columns():
    from src.services.data_loader import load_and_split
    from src.services.features import build_full_matrix
    train, _ = load_and_split()
    X, _ = build_full_matrix(train)
    assert "rv1" not in X.columns
    assert "rv2" not in X.columns
```

**File:** `src/services/features.py` — add:

```python
_FULL_COLS = [
    "lights", "T1", "RH_1", "T2", "RH_2", "T3", "RH_3", "T4", "RH_4",
    "T5", "RH_5", "T6", "RH_6", "T7", "RH_7", "T8", "RH_8", "T9", "RH_9",
    "T_out", "Press_mm_hg", "RH_out", "Windspeed", "Visibility", "Tdewpoint",
]

def build_full_matrix(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    return df[_FULL_COLS], df["Appliances"]
```

---

### Step 2 — train_full.py: train 6 models, save best

**Test** (`tests/test_model.py`):
```python
def test_train_full_produces_loadable_model(tmp_path):
    import joblib
    import pandas as pd
    from src.model.train_full import train_and_save
    out = tmp_path / "model_full.joblib"
    train_and_save(output_path=str(out))
    assert out.exists()
    model = joblib.load(str(out))
    sample = pd.DataFrame([{
        "lights": 0, "T1": 19.89, "RH_1": 47.6, "T2": 19.2, "RH_2": 44.79,
        "T3": 19.79, "RH_3": 44.73, "T4": 17.17, "RH_4": 41.67, "T5": 17.2,
        "RH_5": 55.2, "T6": 7.03, "RH_6": 84.26, "T7": 17.2, "RH_7": 41.63,
        "T8": 18.2, "RH_8": 48.9, "T9": 17.03, "RH_9": 45.53,
        "T_out": 6.6, "Press_mm_hg": 733.5, "RH_out": 92.0,
        "Windspeed": 7.0, "Visibility": 63.0, "Tdewpoint": 5.3,
    }])
    result = model.predict(sample)
    assert isinstance(float(result[0]), float)
```

**File:** `src/model/train_full.py`

```python
import joblib
from sklearn.ensemble import RandomForestRegressor, ExtraTreesRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import r2_score
from xgboost import XGBRegressor
from lightgbm import LGBMRegressor
from catboost import CatBoostRegressor
from src.services.data_loader import load_and_split
from src.services.features import build_full_matrix
from src.model.evaluate import select_best_by_r2


def train_and_save(output_path: str = "src/model/trained/model_full.joblib"):
    train_df, test_df = load_and_split()
    X_train, y_train = build_full_matrix(train_df)
    X_test, y_test = build_full_matrix(test_df)

    models = [
        ("RandomForest", RandomForestRegressor(n_estimators=100, random_state=42)),
        ("XGBoost", XGBRegressor(n_estimators=100, random_state=42, verbosity=0)),
        ("LightGBM", LGBMRegressor(n_estimators=100, random_state=42, verbose=-1)),
        ("CatBoost", CatBoostRegressor(iterations=100, random_state=42, verbose=0)),
        ("ExtraTrees", ExtraTreesRegressor(n_estimators=100, random_state=42)),
        ("Ridge", Ridge()),
    ]

    candidates = []
    for name, model in models:
        model.fit(X_train, y_train)
        score = r2_score(y_test, model.predict(X_test))
        candidates.append((name, model, score))

    _, best_model, _ = select_best_by_r2(candidates)
    joblib.dump(best_model, output_path)
```

---

### Step 3 — run_training_full.py: offline entrypoint

No test required — thin shell delegating to `train_and_save`.

**File:** `scripts/run_training_full.py`

```python
from src.model.train_full import train_and_save
train_and_save()
print("model_full.joblib saved.")
```

## Git

- **Branch:** `feat/005-train-model-full`
- **Commit format:** `feat(model): train 6 regression models on 25 features, save best R² as model_full.joblib`
- **PR title:** `feat(model): train and save model_full.joblib`
