---
id: "013"
slug: implement-run-retraining-script
feature: F3
epic: E5
title: Implement scripts/run_retraining.py — fetch, combine, train, evaluate
status: open
---

# 013 — Implement `scripts/run_retraining.py`

## Goal

Produce a retraining script that fetches clean rows from Supabase, merges them
with the UCI CSV, trains all six regression models on the combined dataset, and
returns the best model and its R² — without writing any files itself, so the
caller decides whether to replace the stored model.

## User Story

As a system operator, I want a retraining script that combines real house data
with the original UCI dataset so that when the model is replaced it has learned
from actual usage rather than just the original training set.

## Reference Docs

- `CLAUDE.md` — ML conventions (Layer 1): 6 models, 80/20 time-ordered split, R² metric, rv1/rv2 drop rule, singleton rule
- `docs/schema.md` — predictions table schema (low_confidence field)
- `docs/architecture.md` — `scripts/` folder role, `data_loader.py` contract

## Acceptance Criteria

- [ ] `test_run_retraining_returns_best_model_and_r2` — function returns dict with keys `best_model`, `new_r2`, `rows_used`; `new_r2` is a float between −1 and 1; `rows_used` equals combined row count
- [ ] `test_run_retraining_drops_rv1_rv2` — combined DataFrame passed to training has no `rv1` or `rv2` columns
- [ ] `test_run_retraining_uses_time_ordered_split` — the 80/20 split preserves chronological order (last 20% of rows used as test)
- [ ] `test_run_retraining_excludes_low_confidence_rows` — rows where `low_confidence=True` in Supabase are not included in combined dataset
- [ ] `test_run_retraining_uses_uci_csv_when_supabase_empty` — if Supabase returns zero clean rows, function trains on UCI CSV alone and still returns valid dict
- [ ] All tests use mocked Supabase client and mocked model training — no real CSV or network required

## Files to Modify

- `scripts/run_retraining.py` — create this file (new)
- `tests/test_retrain_trigger.py` — add the 5 tests above

## Out of Scope

- Writing `model_full.joblib` to disk (issue 014 does that)
- Retraining `model_simple.joblib` or `model_forecast.joblib`
- Hyperparameter tuning
- Feature engineering beyond dropping rv1/rv2

## Implementation Plan

### Step 1 — write all 5 failing tests

Add to `tests/test_retrain_trigger.py`:

```python
import pandas as pd
from unittest.mock import patch, MagicMock


_UCI_COLUMNS = [
    "date", "Appliances", "lights",
    "T1", "RH_1", "T2", "RH_2", "T3", "RH_3", "T4", "RH_4",
    "T5", "RH_5", "T6", "RH_6", "T7", "RH_7", "T8", "RH_8",
    "T9", "RH_9", "T_out", "Press_mm_hg", "RH_out",
    "Windspeed", "Visibility", "Tdewpoint", "rv1", "rv2",
]

def _make_uci_df(n=500):
    import numpy as np
    rng = np.random.default_rng(42)
    df = pd.DataFrame(rng.random((n, len(_UCI_COLUMNS))), columns=_UCI_COLUMNS)
    df["date"] = pd.date_range("2016-01-01", periods=n, freq="10min")
    return df


def test_run_retraining_returns_best_model_and_r2():
    from scripts.run_retraining import run_retraining
    mock_supabase_rows = []
    with patch("scripts.run_retraining.load_uci_csv", return_value=_make_uci_df()), \
         patch("scripts.run_retraining.fetch_clean_rows", return_value=mock_supabase_rows), \
         patch("scripts.run_retraining.train_all_models") as mock_train:
        mock_train.return_value = (MagicMock(), 0.85)
        result = run_retraining()
    assert set(result.keys()) == {"best_model", "new_r2", "rows_used"}
    assert isinstance(result["new_r2"], float)
    assert -1.0 <= result["new_r2"] <= 1.0


def test_run_retraining_drops_rv1_rv2():
    from scripts.run_retraining import run_retraining
    captured = {}

    def capture_train(X_train, y_train, X_test, y_test):
        captured["columns"] = list(X_train.columns)
        return (MagicMock(), 0.80)

    with patch("scripts.run_retraining.load_uci_csv", return_value=_make_uci_df()), \
         patch("scripts.run_retraining.fetch_clean_rows", return_value=[]), \
         patch("scripts.run_retraining.train_all_models", side_effect=capture_train):
        run_retraining()
    assert "rv1" not in captured["columns"]
    assert "rv2" not in captured["columns"]


def test_run_retraining_uses_time_ordered_split():
    from scripts.run_retraining import run_retraining
    captured = {}

    def capture_train(X_train, y_train, X_test, y_test):
        captured["n_train"] = len(X_train)
        captured["n_test"] = len(X_test)
        return (MagicMock(), 0.80)

    df = _make_uci_df(n=500)
    with patch("scripts.run_retraining.load_uci_csv", return_value=df), \
         patch("scripts.run_retraining.fetch_clean_rows", return_value=[]), \
         patch("scripts.run_retraining.train_all_models", side_effect=capture_train):
        run_retraining()
    # 80/20 split of 500 rows → 400 train, 100 test
    assert captured["n_train"] == 400
    assert captured["n_test"] == 100


def test_run_retraining_excludes_low_confidence_rows():
    from scripts.run_retraining import run_retraining
    captured = {}

    def capture_train(X_train, y_train, X_test, y_test):
        captured["total_rows"] = len(X_train) + len(X_test)
        return (MagicMock(), 0.80)

    # 2 clean rows + 1 low_confidence row in Supabase response
    supabase_rows = [
        {"low_confidence": False, "input_features": {"lights": 10, "T1": 19.0}},
        {"low_confidence": True,  "input_features": {"lights": 50, "T1": 30.0}},
        {"low_confidence": False, "input_features": {"lights": 5,  "T1": 18.0}},
    ]
    with patch("scripts.run_retraining.load_uci_csv", return_value=_make_uci_df(n=100)), \
         patch("scripts.run_retraining.fetch_clean_rows", return_value=supabase_rows), \
         patch("scripts.run_retraining.train_all_models", side_effect=capture_train):
        result = run_retraining()
    # rows_used should not count the low_confidence row
    assert result["rows_used"] == 102  # 100 UCI + 2 clean Supabase rows


def test_run_retraining_uses_uci_csv_when_supabase_empty():
    from scripts.run_retraining import run_retraining
    with patch("scripts.run_retraining.load_uci_csv", return_value=_make_uci_df(n=200)), \
         patch("scripts.run_retraining.fetch_clean_rows", return_value=[]), \
         patch("scripts.run_retraining.train_all_models") as mock_train:
        mock_train.return_value = (MagicMock(), 0.75)
        result = run_retraining()
    assert result["rows_used"] == 200
    assert result["new_r2"] == 0.75
```

Run pytest — all 5 must fail before implementing.

---

### Step 2 — implement `scripts/run_retraining.py`

```python
import pandas as pd
from src.services.data_loader import load_uci_csv
from src.services.database import fetch_clean_rows
from src.model.evaluate import train_all_models

_TARGET = "Appliances"
_DROP_COLS = ["rv1", "rv2", "date", _TARGET]
_TRAIN_RATIO = 0.80


def run_retraining() -> dict:
    uci_df = load_uci_csv()
    raw_supabase = fetch_clean_rows()
    clean_rows = [r for r in raw_supabase if not r.get("low_confidence", True)]

    if clean_rows:
        supabase_df = pd.DataFrame(
            [r["input_features"] for r in clean_rows]
        )
        supabase_df[_TARGET] = [r.get("predicted_wh", 0) for r in clean_rows]
        combined = pd.concat([uci_df, supabase_df], ignore_index=True)
    else:
        combined = uci_df.copy()

    rows_used = len(combined)
    combined = combined.drop(columns=[c for c in _DROP_COLS if c in combined.columns])
    combined = combined.drop(columns=["rv1", "rv2"], errors="ignore")

    X = combined.drop(columns=[_TARGET], errors="ignore")
    y = combined[_TARGET]
    split = int(len(X) * _TRAIN_RATIO)
    X_train, X_test = X.iloc[:split], X.iloc[split:]
    y_train, y_test = y.iloc[:split], y.iloc[split:]

    best_model, new_r2 = train_all_models(X_train, y_train, X_test, y_test)
    return {"best_model": best_model, "new_r2": float(new_r2), "rows_used": rows_used}
```

Run pytest — all 5 must pass.

---

## Git

- **Branch:** `feat/013-run-retraining-script`
- **Commit format:** `feat(retrain): implement run_retraining script with 6-model training`
- **PR title:** `feat(retrain): run_retraining script — fetch, combine UCI + Supabase, train all 6 models`
