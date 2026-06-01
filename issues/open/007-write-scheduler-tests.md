---
id: "007"
slug: write-scheduler-tests
feature: F2
epic: E2
title: Write tests for submit_smart_home_reading exception paths and scheduler startup
status: open
---

# 007 — Write tests for `submit_smart_home_reading` and scheduler startup

## Goal

The test suite verifies that `submit_smart_home_reading` silently handles weather
failure, inference failure, and Supabase failure, and that the `BackgroundScheduler`
is running after app startup — so CI catches any regression in the automatic
15-minute reading submission that could crash the Smart Home homeowner's server.

## User Story

As a developer merging changes to the Smart Home scheduler, I want tests that
verify all exception paths are caught and the scheduler starts with the app, so
I can be confident that a transient weather outage or DB error can never take
down the server.

## Reference Docs

- `CLAUDE.md` — TDD rules: failing test first; assertions must name function, input, expected output
- `CLAUDE.md` — scheduler conventions: log and return on failure, never raise

## Acceptance Criteria

- [ ] `test_submit_smart_home_reading_calls_insert_on_success` passes — mocks
      `get_weather` returning `MOCK_WEATHER`, `predict_full` returning `150.0`,
      `wh_to_cost` returning `(0.15, 10.2)`, and `insert_prediction`; asserts
      `insert_prediction` is called exactly once with a row where `tier == "full"`,
      `predicted_wh == 150.0`, and `location == "Lagos"`
- [ ] `test_submit_smart_home_reading_returns_on_weather_exception` passes —
      `get_weather` raises `RuntimeError`; asserts return value is `None` and
      `insert_prediction` is never called
- [ ] `test_submit_smart_home_reading_returns_on_predict_exception` passes —
      `predict_full` raises `RuntimeError`; asserts return value is `None` and
      `insert_prediction` is never called
- [ ] `test_submit_smart_home_reading_returns_on_db_exception` passes —
      `insert_prediction` raises `RuntimeError`; asserts return value is `None`
      and no exception escapes the function
- [ ] `test_scheduler_is_running_after_app_startup` passes — uses `TestClient(app)`
      as context manager; asserts `src.api.main.scheduler.running is True` while
      inside the context
- [ ] All five tests use mocks — no live network, no model file on disk, no Supabase
      connection required

## Files to Modify

- `tests/test_scheduler.py` — create with all five tests

## Out of Scope

- Testing that the job actually fires at a 15-minute interval (requires time manipulation)
- Testing `assemble_full_features` or `predict_full` in isolation (issue 005)
- Testing `insert_prediction` or `get_weather` in isolation (their own test files)

## Implementation Plan

### Step 1 — write all five tests (all must fail before issues 005 and 006 are merged)

**File:** `tests/test_scheduler.py` — create:
```python
import pytest
from unittest.mock import patch, MagicMock

from src.services.scheduler import submit_smart_home_reading

MOCK_WEATHER = {
    "T_out": 28.4, "Press_mm_hg": 1012.0,
    "RH_out": 82.0, "Windspeed": 3.1,
    "Visibility": 10.0, "Tdewpoint": 25.1,
}


@pytest.fixture(autouse=True)
def sensor_env(monkeypatch):
    monkeypatch.setenv("SENSOR_LOCATION", "Lagos")
    monkeypatch.setenv("SENSOR_LIGHTS", "0")
    for i in range(1, 10):
        monkeypatch.setenv(f"SENSOR_T{i}", "20.0")
        monkeypatch.setenv(f"SENSOR_RH_{i}", "50.0")


def test_submit_smart_home_reading_calls_insert_on_success():
    mock_insert = MagicMock()
    with patch("src.services.scheduler.get_weather", return_value=MOCK_WEATHER), \
         patch("src.services.scheduler.predict_full", return_value=150.0), \
         patch("src.services.scheduler.wh_to_cost", return_value=(0.15, 10.2)), \
         patch("src.services.scheduler.insert_prediction", mock_insert):
        submit_smart_home_reading()
    mock_insert.assert_called_once()
    call_row = mock_insert.call_args[0][0]
    assert call_row["tier"] == "full"
    assert call_row["predicted_wh"] == 150.0
    assert call_row["location"] == "Lagos"


def test_submit_smart_home_reading_returns_on_weather_exception():
    mock_insert = MagicMock()
    with patch("src.services.scheduler.get_weather",
               side_effect=RuntimeError("connection timeout")), \
         patch("src.services.scheduler.insert_prediction", mock_insert):
        result = submit_smart_home_reading()
    assert result is None
    mock_insert.assert_not_called()


def test_submit_smart_home_reading_returns_on_predict_exception():
    mock_insert = MagicMock()
    with patch("src.services.scheduler.get_weather", return_value=MOCK_WEATHER), \
         patch("src.services.scheduler.predict_full",
               side_effect=RuntimeError("model not loaded")), \
         patch("src.services.scheduler.insert_prediction", mock_insert):
        result = submit_smart_home_reading()
    assert result is None
    mock_insert.assert_not_called()


def test_submit_smart_home_reading_returns_on_db_exception():
    with patch("src.services.scheduler.get_weather", return_value=MOCK_WEATHER), \
         patch("src.services.scheduler.predict_full", return_value=150.0), \
         patch("src.services.scheduler.wh_to_cost", return_value=(0.15, 10.2)), \
         patch("src.services.scheduler.insert_prediction",
               side_effect=RuntimeError("supabase write failed")):
        result = submit_smart_home_reading()
    assert result is None


def test_scheduler_is_running_after_app_startup():
    from fastapi.testclient import TestClient
    from src.api.main import app, scheduler
    with TestClient(app):
        assert scheduler.running is True
```

### Step 2 — confirm all five tests fail before issues 005 and 006 are merged

```bash
pytest tests/test_scheduler.py -v
```

Expected before implementation: 5 errors (ImportError or AttributeError) because
`src.services.scheduler`, `src.model.predict.predict_full`, and the lifespan wiring
do not exist yet.

After issues 005 and 006 are merged, re-run:

```bash
pytest tests/test_scheduler.py -v
```

Expected: 5 tests passing, 0 failing, 0 errors.

## Git

- **Branch:** `test/007-scheduler-tests`
- **Commit format:** `test(scheduler): add exception-path and startup tests for submit_smart_home_reading`
- **PR title:** `test: add scheduler exception-path and startup tests`
