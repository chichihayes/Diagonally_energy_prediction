---
id: "012"
slug: implement-should-retrain-condition-check
feature: F3
epic: E5
title: Implement should_retrain 3-condition check in retrain_trigger.py
status: open
---

# 012 — Implement `should_retrain` 3-condition check in `retrain_trigger.py`

## Goal

Expose a pure function `should_retrain` in `retrain_trigger.py` that returns
`True` only when all three retraining conditions are simultaneously satisfied,
so the rest of the retraining pipeline has a single, testable gate to query.

## User Story

As a system operator, I want the retraining pipeline to fire only when drift
is confirmed, enough clean data has accumulated, and the data quality is high
enough — so the model is never retrained on noisy or insufficient data.

## Reference Docs

- `CLAUDE.md` — Retraining Trigger: 3 conditions, anomaly rate formula, reset rules
- `docs/architecture.md` — service boundary for `retrain_trigger.py`
- `docs/decisions.md` — why drift + row count + anomaly rate are all required

## Acceptance Criteria

- [ ] `test_should_retrain_all_conditions_true_returns_true` — `should_retrain(True, 2000, 2200)` returns `True`
- [ ] `test_should_retrain_drift_false_returns_false` — `should_retrain(False, 2000, 2200)` returns `False`
- [ ] `test_should_retrain_clean_count_below_threshold_returns_false` — `should_retrain(True, 1999, 1999)` returns `False`
- [ ] `test_should_retrain_anomaly_rate_too_high_returns_false` — `should_retrain(True, 2000, 3000)` returns `False`
- [ ] `test_should_retrain_c1_c2_both_false_returns_false` — `should_retrain(False, 1999, 1999)` returns `False`
- [ ] `test_should_retrain_c1_c3_both_false_returns_false` — `should_retrain(False, 2000, 3000)` returns `False`
- [ ] `test_should_retrain_c2_c3_both_false_returns_false` — `should_retrain(True, 1000, 3000)` returns `False`
- [ ] `test_should_retrain_all_conditions_false_returns_false` — `should_retrain(False, 1000, 3000)` returns `False`
- [ ] All 8 tests fail before `should_retrain` is implemented, pass after

## Files to Modify

- `src/services/retrain_trigger.py` — add `should_retrain` function
- `tests/test_retrain_trigger.py` — add all 8 tests

## Out of Scope

- Fetching row counts from Supabase (caller's responsibility)
- Drift detection logic (lives in `monitor.py`)
- The retraining script itself (issue 013)
- Writing to `retrain_log` (issue 014)

## Implementation Plan

### Step 1 — write all 8 failing tests

**Test file:** `tests/test_retrain_trigger.py`

```python
import pytest
from src.services.retrain_trigger import should_retrain


def test_should_retrain_all_conditions_true_returns_true():
    # 2000 / 2200 = 0.909 — passes 90% threshold
    assert should_retrain(True, 2000, 2200) is True


def test_should_retrain_drift_false_returns_false():
    assert should_retrain(False, 2000, 2200) is False


def test_should_retrain_clean_count_below_threshold_returns_false():
    # 1999 < 2000 — fails C2
    assert should_retrain(True, 1999, 1999) is False


def test_should_retrain_anomaly_rate_too_high_returns_false():
    # 2000 / 3000 = 0.667 — fails C3
    assert should_retrain(True, 2000, 3000) is False


def test_should_retrain_c1_c2_both_false_returns_false():
    assert should_retrain(False, 1999, 1999) is False


def test_should_retrain_c1_c3_both_false_returns_false():
    assert should_retrain(False, 2000, 3000) is False


def test_should_retrain_c2_c3_both_false_returns_false():
    # 1000 / 3000 = 0.333 — fails C2 and C3
    assert should_retrain(True, 1000, 3000) is False


def test_should_retrain_all_conditions_false_returns_false():
    assert should_retrain(False, 1000, 3000) is False
```

Run `pytest tests/test_retrain_trigger.py` — all 8 must fail (ImportError or
AssertionError) before implementing.

---

### Step 2 — implement `should_retrain` in `retrain_trigger.py`

**File:** `src/services/retrain_trigger.py`

```python
_CLEAN_ROW_THRESHOLD = 2000
_ANOMALY_RATE_MAX = 0.10   # anomaly rate must be below this


def should_retrain(
    drift_detected: bool,
    clean_row_count: int,
    total_row_count: int,
) -> bool:
    if not drift_detected:
        return False
    if clean_row_count < _CLEAN_ROW_THRESHOLD:
        return False
    if total_row_count == 0:
        return False
    anomaly_rate = 1.0 - (clean_row_count / total_row_count)
    return anomaly_rate < _ANOMALY_RATE_MAX
```

Run `pytest tests/test_retrain_trigger.py` — all 8 must now pass.

---

## Git

- **Branch:** `feat/012-should-retrain-condition-check`
- **Commit format:** `feat(retrain): implement should_retrain 3-condition gate`
- **PR title:** `feat(retrain): add should_retrain guard with all-condition test suite`
