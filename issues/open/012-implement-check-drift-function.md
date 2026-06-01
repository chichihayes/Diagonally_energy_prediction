---
epic: E5-monitoring-and-retraining
feature: F2
slug: implement-check-drift-function
---

# 012 — Implement check_drift Function

## Goal

As a system operator, I want the system to compute rolling mean deviation across all 25 features for the last 100 clean readings so it can detect when real house data has shifted away from the training distribution.

## User Story

As a system operator, I want `check_drift` to accept 100 clean feature dicts, compare their rolling means to training means loaded from `training_stats.json`, and return which features have exceeded 15% deviation, so I can understand when a model retrain is becoming necessary.

## Reference Docs

- `docs/schema.md` — 25 input feature names under "model_full — Smart Home Tier"
- `docs/decisions.md` — drift threshold rationale

## Acceptance Criteria

- [ ] `check_drift(clean_readings)` raises `ValueError` when fewer than 100 readings are passed
- [ ] Returns `{"drift_detected": False, "drifted_features": [], "deviations": {...}}` for 100 readings at exact training-mean values
- [ ] Returns `{"drift_detected": True, "drifted_features": ["T1"], ...}` when `T1` is 20% above training mean in all 100 readings
- [ ] `deviations` dict contains all 25 features as keys (even non-drifted ones)
- [ ] Deviation formula: `abs(rolling_mean - training_mean) / training_mean * 100`
- [ ] Threshold is 15% — features with deviation > 15 are flagged; features at exactly 15 are not
- [ ] Training means are loaded from `src/model/trained/training_stats.json` (same file used by F1 anomaly detection)

## Files to Modify

- `src/services/retrain_trigger.py` — add `check_drift`
- `tests/test_retrain_trigger.py` — add tests (write first, confirm they fail, then implement)

## Out of Scope

- PSI or KS-Test drift methods
- Per-feature threshold configuration
- Storing the result to Supabase (Issue 013)
- Wiring the counter into the scheduler (Issue 014)

## Implementation Plan

### Step 1 — Write failing tests in `tests/test_retrain_trigger.py`

**Test:** `test_check_drift_raises_on_too_few_readings`
- Build a list of 99 identical feature dicts (any values)
- Call `check_drift(readings)`
- Assert: `pytest.raises(ValueError)`

**Test:** `test_check_drift_no_drift_at_training_mean`
- Load `src/model/trained/training_stats.json`; build 100 readings where every feature equals `stats["mean"][feature]`
- Call `check_drift(readings)`
- Assert: `result["drift_detected"] == False`
- Assert: `result["drifted_features"] == []`

**Test:** `test_check_drift_detects_feature_above_threshold`
- Build 100 readings where `T1 = stats["mean"]["T1"] * 1.20`, all other features at training mean
- Call `check_drift(readings)`
- Assert: `result["drift_detected"] == True`
- Assert: `"T1" in result["drifted_features"]`
- Assert: `abs(result["deviations"]["T1"] - 20.0) < 0.01`

**Test:** `test_check_drift_feature_just_below_threshold_not_flagged`
- Build 100 readings where `RH_1 = stats["mean"]["RH_1"] * 1.14` (14%), all others at training mean
- Call `check_drift(readings)`
- Assert: `result["drift_detected"] == False`
- Assert: `"RH_1" not in result["drifted_features"]`

**Test:** `test_check_drift_deviations_contains_all_25_features`
- Build 100 readings at training mean
- Call `check_drift(readings)`
- Assert: `len(result["deviations"]) == 25`
- Assert: `"lights"` and `"Tdewpoint"` are both keys in `result["deviations"]`

### Step 2 — Implement `check_drift` in `src/services/retrain_trigger.py`

1. At module level, load `training_stats.json` (path: `src/model/trained/training_stats.json`) and extract the `"mean"` dict.
2. Define the list of 25 feature names matching `docs/schema.md` model_full section.
3. Implement:

```python
def check_drift(clean_readings: list[dict]) -> dict:
    if len(clean_readings) < 100:
        raise ValueError(f"check_drift requires 100 readings, got {len(clean_readings)}")
    deviations = {}
    drifted = []
    for feature in FULL_FEATURES:
        rolling_mean = sum(r[feature] for r in clean_readings) / len(clean_readings)
        training_mean = _training_means[feature]
        deviation = abs(rolling_mean - training_mean) / training_mean * 100
        deviations[feature] = round(deviation, 4)
        if deviation > 15:
            drifted.append(feature)
    return {"drift_detected": bool(drifted), "drifted_features": drifted, "deviations": deviations}
```

### Step 3 — Confirm all 5 tests pass

Run `pytest tests/test_retrain_trigger.py -v` and verify green.

## Git

- Branch: `feat/E5-F2-check-drift-function`
- Commit: `feat(monitor): implement check_drift rolling mean deviation for 25 features`
- PR: `feat: Add check_drift — rolling mean deviation detection across 25 features`
