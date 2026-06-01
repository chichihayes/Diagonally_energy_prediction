---
id: "011"
slug: write-leaderboard-api-tests
feature: F4
epic: E3
title: Write tests for GET /api/v1/models/leaderboard
status: open
---

# 011 — Write tests for GET /api/v1/models/leaderboard

## Goal

`GET /api/v1/models/leaderboard` has a test suite that verifies the 200
success path, the 503 missing-file path, and that `winner=True` appears
exactly once in each model group — so regressions are caught by CI.

## User Story

As a developer maintaining the leaderboard route, I want automated tests that
cover the success path, the missing-file error, and the winner constraint —
so that any regression is caught by CI before it reaches production.

## Reference Docs

- `docs/api-contracts.md` — GET /api/v1/models/leaderboard expected response shape and error codes

## Acceptance Criteria

- [ ] Test: when `leaderboard.json` exists, endpoint returns HTTP 200
- [ ] Test: 200 response body has top-level keys `regression` and `forecast`
- [ ] Test: `winner=True` appears exactly once in the `regression` list
- [ ] Test: `winner=True` appears exactly once in the `forecast` list
- [ ] Test: when `leaderboard.json` does not exist, endpoint returns HTTP 503
- [ ] Test: 503 response body `detail` field contains the phrase `"run training scripts"`
- [ ] All tests pass without a real `leaderboard.json` on disk — the file is written to `tmp_path` and `MODEL_PATH_FULL` is patched accordingly

## Files to Modify

- `tests/test_api.py` — add the fixture constant and all five tests listed below

## Out of Scope

- Tests for `write_leaderboard` in `evaluate.py` (covered in issue 008)
- Testing sort order — that is a frontend concern
- Frontend tests

## Implementation Plan

### Step 1 — test fixtures: shared leaderboard constant

No production change. Add to `tests/test_api.py`:

```python
_LEADERBOARD = {
    "regression": [
        {"model": "RandomForest", "r2": 0.91, "winner": False},
        {"model": "XGBoost",      "r2": 0.94, "winner": True},
        {"model": "LightGBM",     "r2": 0.92, "winner": False},
        {"model": "CatBoost",     "r2": 0.90, "winner": False},
        {"model": "ExtraTrees",   "r2": 0.89, "winner": False},
        {"model": "Ridge",        "r2": 0.78, "winner": False},
    ],
    "forecast": [
        {"model": "Prophet",  "mape": 0.12, "winner": False},
        {"model": "XGBoost",  "mape": 0.08, "winner": True},
        {"model": "LightGBM", "mape": 0.10, "winner": False},
        {"model": "LSTM",     "mape": 0.11, "winner": False},
        {"model": "TFT",      "mape": 0.09, "winner": False},
    ],
}
```

---

### Step 2 — success path: 200 with regression and forecast keys

**Test** (`tests/test_api.py`):
```python
def test_get_leaderboard_returns_200_with_regression_and_forecast_keys(tmp_path):
    import json
    from unittest.mock import patch
    from fastapi.testclient import TestClient
    from src.api.main import app

    lb_file = tmp_path / "leaderboard.json"
    lb_file.write_text(json.dumps(_LEADERBOARD))
    model_path = tmp_path / "model_full.joblib"

    client = TestClient(app)
    with patch.dict("os.environ", {"MODEL_PATH_FULL": str(model_path)}):
        response = client.get("/api/v1/models/leaderboard")

    assert response.status_code == 200
    data = response.json()
    assert "regression" in data
    assert "forecast" in data
```

---

### Step 3 — winner constraint: exactly one winner per group

**Tests** (`tests/test_api.py`):
```python
def test_get_leaderboard_regression_has_exactly_one_winner(tmp_path):
    import json
    from unittest.mock import patch
    from fastapi.testclient import TestClient
    from src.api.main import app

    (tmp_path / "leaderboard.json").write_text(json.dumps(_LEADERBOARD))
    model_path = tmp_path / "model_full.joblib"

    client = TestClient(app)
    with patch.dict("os.environ", {"MODEL_PATH_FULL": str(model_path)}):
        response = client.get("/api/v1/models/leaderboard")

    data = response.json()
    assert sum(1 for e in data["regression"] if e["winner"]) == 1

def test_get_leaderboard_forecast_has_exactly_one_winner(tmp_path):
    import json
    from unittest.mock import patch
    from fastapi.testclient import TestClient
    from src.api.main import app

    (tmp_path / "leaderboard.json").write_text(json.dumps(_LEADERBOARD))
    model_path = tmp_path / "model_full.joblib"

    client = TestClient(app)
    with patch.dict("os.environ", {"MODEL_PATH_FULL": str(model_path)}):
        response = client.get("/api/v1/models/leaderboard")

    data = response.json()
    assert sum(1 for e in data["forecast"] if e["winner"]) == 1
```

---

### Step 4 — missing file returns 503 with informative detail

**Test** (`tests/test_api.py`):
```python
def test_get_leaderboard_returns_503_when_leaderboard_file_absent(tmp_path):
    from unittest.mock import patch
    from fastapi.testclient import TestClient
    from src.api.main import app

    model_path = tmp_path / "model_full.joblib"  # leaderboard.json intentionally not created

    client = TestClient(app)
    with patch.dict("os.environ", {"MODEL_PATH_FULL": str(model_path)}):
        response = client.get("/api/v1/models/leaderboard")

    assert response.status_code == 503
    assert "run training scripts" in response.json()["detail"].lower()
```

## Git

- **Branch:** `feat/011-leaderboard-api-tests`
- **Commit format:** `test(api): add test suite for GET /api/v1/models/leaderboard`
- **PR title:** `test(api): test suite for GET /api/v1/models/leaderboard`
