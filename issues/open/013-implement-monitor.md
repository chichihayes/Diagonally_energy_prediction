---
id: "013"
slug: implement-monitor
feature: F1
epic: E5
title: Implement monitor.py — Z-Score anomaly detection
status: open
---

# 013 — Implement monitor.py — Z-Score anomaly detection

## Goal

A `check_anomaly` function exists in `src/services/monitor.py` that loads
`training_stats.json` once at module import and returns a Z-Score report for
any incoming feature dict — so callers can flag a prediction as low confidence
without duplicating the detection logic.

## User Story

As the prediction route handler, I want `check_anomaly(features)` to tell me
if any input feature is outside 3 standard deviations from the training mean so
I can add a `low_confidence` flag to the response without implementing the
formula in each route.

## Reference Docs

- `CLAUDE.md` — monitoring conventions: Z = (value - mean) / std, threshold abs(Z) > 3,
  skip std == 0, singleton load from training_stats.json

## Acceptance Criteria

- [ ] `_training_stats` is loaded once at module import — never reloaded per call
- [ ] `check_anomaly({"T1": 50.0, ...})` where T1 is 30 std devs above the training mean
  returns `{"is_anomaly": True, "z_scores": {"T1": <float>}, "flagged_features": ["T1"]}`
- [ ] `check_anomaly` with all values within 3 std devs of their means returns
  `{"is_anomaly": False, "z_scores": {...}, "flagged_features": []}`
- [ ] A feature whose training `std == 0` is skipped: not in `z_scores`, not in `flagged_features`
- [ ] Return dict always has exactly three keys: `is_anomaly`, `z_scores`, `flagged_features`
- [ ] Module raises `FileNotFoundError` if `training_stats.json` does not exist at import time
- [ ] Features present in the input dict but absent from `_training_stats` are silently ignored

## Files to Modify

- `src/services/monitor.py` — create

## Out of Scope

- Calling `store_anomaly` or touching the database (that is routes.py responsibility, issue 015)
- Drift detection or retraining logic (F2, F3)
- Any API route changes

**Dependency:** Issue 012 must be completed and `training_stats.json` must exist at
`src/model/trained/training_stats.json` before this module can be imported.

## Implementation Plan

### Step 1 — write failing tests

**File:** `tests/test_monitor.py` (extend the file started in issue 012)

```python
from unittest.mock import patch

MOCK_STATS = {
    "T1": {"mean": 20.0, "std": 1.0},
    "lights": {"mean": 50.0, "std": 10.0},
    "RH_1": {"mean": 45.0, "std": 5.0},
}

def test_check_anomaly_flags_extreme_value():
    from src.services import monitor
    with patch.object(monitor, "_training_stats", MOCK_STATS):
        result = monitor.check_anomaly({"T1": 50.0, "lights": 50.0, "RH_1": 45.0})
    assert result["is_anomaly"] is True
    assert "T1" in result["flagged_features"]
    assert result["z_scores"]["T1"] == pytest.approx(30.0, abs=0.1)

def test_check_anomaly_normal_values_return_false():
    from src.services import monitor
    with patch.object(monitor, "_training_stats", MOCK_STATS):
        result = monitor.check_anomaly({"T1": 20.5, "lights": 52.0, "RH_1": 44.0})
    assert result["is_anomaly"] is False
    assert result["flagged_features"] == []

def test_check_anomaly_skips_zero_std_feature():
    stats = {"T1": {"mean": 20.0, "std": 0.0}, "lights": {"mean": 50.0, "std": 10.0}}
    from src.services import monitor
    with patch.object(monitor, "_training_stats", stats):
        result = monitor.check_anomaly({"T1": 9999.0, "lights": 50.0})
    assert "T1" not in result["z_scores"]
    assert "T1" not in result["flagged_features"]

def test_check_anomaly_result_has_required_keys():
    from src.services import monitor
    with patch.object(monitor, "_training_stats", MOCK_STATS):
        result = monitor.check_anomaly({"T1": 20.0, "lights": 50.0, "RH_1": 45.0})
    assert set(result.keys()) == {"is_anomaly", "z_scores", "flagged_features"}

def test_check_anomaly_ignores_unknown_features():
    from src.services import monitor
    with patch.object(monitor, "_training_stats", MOCK_STATS):
        result = monitor.check_anomaly({"T1": 20.0, "unknown_col": 999.0})
    assert "unknown_col" not in result["z_scores"]
    assert result["is_anomaly"] is False
```

All five tests must fail (ImportError or AttributeError) before implementing.

---

### Step 2 — implement monitor.py

**File:** `src/services/monitor.py`

```python
import json

_STATS_PATH = "src/model/trained/training_stats.json"

with open(_STATS_PATH) as f:
    _training_stats: dict = json.load(f)


def check_anomaly(features: dict) -> dict:
    z_scores = {}
    flagged = []
    for feat, value in features.items():
        if feat not in _training_stats:
            continue
        mean = _training_stats[feat]["mean"]
        std = _training_stats[feat]["std"]
        if std == 0:
            continue
        z = (value - mean) / std
        z_scores[feat] = round(z, 4)
        if abs(z) > 3:
            flagged.append(feat)
    return {
        "is_anomaly": len(flagged) > 0,
        "z_scores": z_scores,
        "flagged_features": flagged,
    }
```

Confirm all five tests pass.

## Git

- **Branch:** `feat/013-implement-monitor`
- **Commit format:** `feat(services): implement monitor.py — Z-Score anomaly detection with training_stats singleton`
- **PR title:** `feat(services): implement monitor.py — Z-Score anomaly detection`
