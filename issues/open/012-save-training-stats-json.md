---
id: "012"
slug: save-training-stats-json
feature: F1
epic: E5
title: Save training_stats.json from UCI training split
status: open
---

# 012 — Save training_stats.json from UCI training split

## Goal

After running `scripts/run_training_full.py`, a file exists at
`src/model/trained/training_stats.json` that records the mean and standard
deviation for all 25 input features computed from the training split of the UCI
dataset — so the anomaly detector always compares new readings against the fixed
original distribution.

## User Story

As a developer setting up the project, I want `training_stats.json` generated
alongside `model_full.joblib` so the anomaly detector has a permanent reference
distribution that is never overwritten by future retraining runs.

## Reference Docs

- `docs/schema.md` — full feature list (25 features, lights through Tdewpoint)
- `CLAUDE.md` — ML conventions: 80/20 time-ordered split; monitoring conventions:
  training_stats.json fixed reference, never overwrite during retraining

## Acceptance Criteria

- [ ] Running `scripts/run_training_full.py` produces `src/model/trained/training_stats.json`
- [ ] The file contains exactly 25 top-level keys — one per full model feature
- [ ] Each key maps to `{"mean": float, "std": float}`
- [ ] Mean and std are computed from the training split only (first 80% of rows, time-ordered)
- [ ] `scripts/run_retraining.py` does not write or overwrite `training_stats.json`
- [ ] `json.load(open("src/model/trained/training_stats.json"))` succeeds and `stats["T1"]["mean"]` returns a float

## Files to Modify

- `scripts/run_training_full.py` — add stats computation and JSON save after loading
  the training split (write only if file does not already exist)

## Out of Scope

- Computing stats for the 7-feature simple model
- Using the stats for Z-Score checks (issue 013)
- Any API route changes
- Retraining script changes beyond confirming it does not write this file

## Implementation Plan

### Step 1 — write failing test

**File:** `tests/test_monitor.py`

```python
import json
import os
import pytest

FULL_FEATURES = [
    "lights", "T1", "RH_1", "T2", "RH_2", "T3", "RH_3", "T4", "RH_4",
    "T5", "RH_5", "T6", "RH_6", "T7", "RH_7", "T8", "RH_8", "T9", "RH_9",
    "T_out", "Press_mm_hg", "RH_out", "Windspeed", "Visibility", "Tdewpoint",
]

def test_training_stats_json_has_correct_structure():
    stats_path = "src/model/trained/training_stats.json"
    if not os.path.exists(stats_path):
        pytest.skip("training_stats.json not yet generated — run scripts/run_training_full.py first")
    with open(stats_path) as f:
        stats = json.load(f)
    assert set(stats.keys()) == set(FULL_FEATURES)
    for feat in FULL_FEATURES:
        assert "mean" in stats[feat], f"missing 'mean' for {feat}"
        assert "std" in stats[feat], f"missing 'std' for {feat}"
        assert isinstance(stats[feat]["mean"], float), f"mean for {feat} is not float"
        assert isinstance(stats[feat]["std"], float), f"std for {feat} is not float"
```

The test skips (does not pass) when the file is absent. After implementing the
script, the test must pass without the skip.

---

### Step 2 — add stats generation to run_training_full.py

**File:** `scripts/run_training_full.py`

After the call to `load_and_split()` returns `train_df, test_df`, add the block
below. Write the file only when it does not already exist so a subsequent call
to `scripts/run_retraining.py` cannot overwrite the original UCI reference:

```python
import json
import os

STATS_PATH = "src/model/trained/training_stats.json"
FULL_FEATURES = [
    "lights", "T1", "RH_1", "T2", "RH_2", "T3", "RH_3", "T4", "RH_4",
    "T5", "RH_5", "T6", "RH_6", "T7", "RH_7", "T8", "RH_8", "T9", "RH_9",
    "T_out", "Press_mm_hg", "RH_out", "Windspeed", "Visibility", "Tdewpoint",
]

if not os.path.exists(STATS_PATH):
    stats = {
        feat: {
            "mean": float(train_df[feat].mean()),
            "std": float(train_df[feat].std()),
        }
        for feat in FULL_FEATURES
    }
    with open(STATS_PATH, "w") as f:
        json.dump(stats, f, indent=2)
    print(f"training_stats.json saved to {STATS_PATH}")
else:
    print(f"training_stats.json already exists at {STATS_PATH} — skipping.")
```

Confirm the test passes after running the script once.

## Git

- **Branch:** `feat/012-save-training-stats-json`
- **Commit format:** `feat(model): compute and save training_stats.json from UCI training split`
- **PR title:** `feat(model): save training_stats.json — fixed Z-Score reference distribution`
