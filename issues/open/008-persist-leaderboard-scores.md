---
id: "008"
slug: persist-leaderboard-scores
feature: F4
epic: E3
title: Persist leaderboard scores to leaderboard.json during training
status: open
---

# 008 — Persist leaderboard scores to leaderboard.json during training

## Goal

Both full-model training scripts write their evaluation results to
`src/model/trained/leaderboard.json` after each run so the leaderboard API
can serve current scores without triggering any retraining.

## User Story

As a developer running training, I want model scores saved to a JSON file
automatically after each training run so that the leaderboard API always
reflects the latest results without any manual step.

## Reference Docs

- `docs/architecture.md` — `src/model/trained/` directory layout, training is always offline
- `docs/schema.md` — feature definitions (leaderboard.json format is defined in this issue)

## Acceptance Criteria

- [ ] `write_leaderboard("regression", {"RandomForest": 0.91, "XGBoost": 0.94}, "r2", path)` writes a `regression` key to the file with `winner=True` on the highest-R² entry
- [ ] `write_leaderboard("forecast", {"Prophet": 0.12, "XGBoost": 0.08}, "mape", path)` writes a `forecast` key to the file with `winner=True` on the lowest-MAPE entry
- [ ] Calling `write_leaderboard` a second time with the same `section` overwrites that section only — the other section is preserved
- [ ] Every entry in the written list has exactly the keys: `model`, the metric key (`r2` or `mape`), and `winner`
- [ ] `winner=True` appears exactly once per section
- [ ] `scripts/run_training_full.py` calls `write_leaderboard("regression", scores, "r2", leaderboard_path)` after saving `model_full.joblib`
- [ ] `scripts/run_training_forecast.py` calls `write_leaderboard("forecast", scores, "mape", leaderboard_path)` after saving `model_forecast.joblib`

## Files to Modify

- `src/model/evaluate.py` — add `write_leaderboard(section, scores, metric, path)` function
- `scripts/run_training_full.py` — call `write_leaderboard` after `evaluate_models()`
- `scripts/run_training_forecast.py` — call `write_leaderboard` after evaluating time series models

## Out of Scope

- `scripts/run_training_simple.py` — simple model scores are not surfaced in the API (F4 out of scope)
- Leaderboard history — one current snapshot only, overwritten each training run
- Any API or frontend changes (issues 009 and 010)

## Implementation Plan

### Step 1 — evaluate.py: add write_leaderboard function

**Tests** (`tests/test_evaluate.py`):
```python
import json
import pathlib

def test_write_leaderboard_regression_sets_winner_on_highest_r2(tmp_path):
    from src.model.evaluate import write_leaderboard
    scores = {"RandomForest": 0.91, "XGBoost": 0.94, "Ridge": 0.87}
    leaderboard_path = tmp_path / "leaderboard.json"
    write_leaderboard("regression", scores, "r2", leaderboard_path)
    data = json.loads(leaderboard_path.read_text())
    winners = [e for e in data["regression"] if e["winner"]]
    assert len(winners) == 1
    assert winners[0]["model"] == "XGBoost"

def test_write_leaderboard_forecast_sets_winner_on_lowest_mape(tmp_path):
    from src.model.evaluate import write_leaderboard
    scores = {"Prophet": 0.12, "XGBoost": 0.08, "LightGBM": 0.10}
    leaderboard_path = tmp_path / "leaderboard.json"
    write_leaderboard("forecast", scores, "mape", leaderboard_path)
    data = json.loads(leaderboard_path.read_text())
    winners = [e for e in data["forecast"] if e["winner"]]
    assert len(winners) == 1
    assert winners[0]["model"] == "XGBoost"

def test_write_leaderboard_preserves_other_sections(tmp_path):
    from src.model.evaluate import write_leaderboard
    leaderboard_path = tmp_path / "leaderboard.json"
    write_leaderboard("regression", {"RF": 0.91}, "r2", leaderboard_path)
    write_leaderboard("forecast", {"Prophet": 0.15}, "mape", leaderboard_path)
    data = json.loads(leaderboard_path.read_text())
    assert "regression" in data
    assert "forecast" in data

def test_write_leaderboard_each_entry_has_model_metric_and_winner_keys(tmp_path):
    from src.model.evaluate import write_leaderboard
    scores = {"RF": 0.91, "XGB": 0.94}
    leaderboard_path = tmp_path / "leaderboard.json"
    write_leaderboard("regression", scores, "r2", leaderboard_path)
    data = json.loads(leaderboard_path.read_text())
    for entry in data["regression"]:
        assert set(entry.keys()) == {"model", "r2", "winner"}
```

**File:** `src/model/evaluate.py` — add at the bottom:

```python
import json
import pathlib

def write_leaderboard(section: str, scores: dict, metric: str, path: pathlib.Path) -> None:
    existing = json.loads(path.read_text()) if path.exists() else {}
    best = min(scores, key=scores.get) if metric == "mape" else max(scores, key=scores.get)
    existing[section] = [
        {"model": name, metric: round(score, 6), "winner": name == best}
        for name, score in scores.items()
    ]
    path.write_text(json.dumps(existing, indent=2))
```

---

### Step 2 — run_training_full.py: call write_leaderboard after evaluate

No new test — the function is already tested in step 1.

**File:** `scripts/run_training_full.py` — after the block that saves `model_full.joblib`, add:

```python
from src.model.evaluate import write_leaderboard
import pathlib

leaderboard_path = pathlib.Path("src/model/trained/leaderboard.json")
write_leaderboard("regression", scores, "r2", leaderboard_path)
print(f"Leaderboard written to {leaderboard_path}")
```

`scores` is the `{model_name: r2_float}` dict already produced by `evaluate_models()`.

---

### Step 3 — run_training_forecast.py: call write_leaderboard after evaluate

No new test.

**File:** `scripts/run_training_forecast.py` — after saving `model_forecast.joblib`, add:

```python
from src.model.evaluate import write_leaderboard
import pathlib

leaderboard_path = pathlib.Path("src/model/trained/leaderboard.json")
write_leaderboard("forecast", scores, "mape", leaderboard_path)
print(f"Forecast leaderboard written to {leaderboard_path}")
```

`scores` is the `{model_name: mape_float}` dict produced by the time series evaluation loop.

## Git

- **Branch:** `feat/008-persist-leaderboard-scores`
- **Commit format:** `feat(evaluate): write model scores to leaderboard.json after training`
- **PR title:** `feat(evaluate): persist leaderboard scores to leaderboard.json`
