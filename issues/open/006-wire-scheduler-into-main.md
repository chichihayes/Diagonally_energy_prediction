---
id: "006"
slug: wire-scheduler-into-main
feature: F2
epic: E2
title: Wire APScheduler BackgroundScheduler into FastAPI lifespan in main.py
status: open
---

# 006 — Wire APScheduler into FastAPI lifespan in `main.py`

## Goal

The FastAPI application starts an APScheduler `BackgroundScheduler` on startup
that fires `submit_smart_home_reading` every 15 minutes and shuts it down cleanly
when the app stops — with no impact on any existing routes.

## User Story

As a Smart Home homeowner, I want predictions to be submitted automatically in the
background from the moment the server starts so I receive continuous predictions
without any manual action.

## Reference Docs

- `docs/architecture.md` — APScheduler runs inside the FastAPI process, started in the `main.py` lifespan event
- `CLAUDE.md` — scheduler conventions: 15-minute interval, graceful shutdown on app stop

## Acceptance Criteria

- [ ] On app startup the `BackgroundScheduler` is created and `scheduler.start()` is called
- [ ] `submit_smart_home_reading` is registered as an interval job with `minutes=15`
- [ ] On app shutdown `scheduler.shutdown()` is called with no unhandled exceptions
- [ ] The `scheduler` object is exported at `src.api.main.scheduler` so tests can
      inspect `scheduler.running`
- [ ] Existing routes registered via `router` (e.g. `/health`, `POST /api/v1/predict/simple`)
      continue to respond correctly after the lifespan wiring

## Files to Modify

- `src/api/main.py` — add FastAPI lifespan context manager with `BackgroundScheduler`

## Out of Scope

- Changing the scheduler interval or job target
- Scheduler tests (issue 007)
- Any other route, service, or model file

## Implementation Plan

### Step 1 — update `main.py` with lifespan

**File:** `src/api/main.py` — replace current content with:
```python
from contextlib import asynccontextmanager

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI

from src.api.routes import router
from src.services.scheduler import submit_smart_home_reading

scheduler = BackgroundScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler.add_job(submit_smart_home_reading, "interval", minutes=15)
    scheduler.start()
    yield
    scheduler.shutdown()


app = FastAPI(lifespan=lifespan)
app.include_router(router)
```

No new tests in this issue — the scheduler startup assertion is in issue 007.
The existing endpoint tests in `tests/test_api.py` (issue 004) must still pass
after this change; run them to confirm no regression:

```bash
pytest tests/test_api.py -v
```

## Git

- **Branch:** `feat/006-wire-scheduler-into-main`
- **Commit format:** `feat(api): wire APScheduler BackgroundScheduler into FastAPI lifespan with 15-min interval`
- **PR title:** `feat(api): wire APScheduler into FastAPI lifespan`
