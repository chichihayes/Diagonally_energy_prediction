---
id: "009"
slug: leaderboard-api-route
feature: F4
epic: E3
title: Implement GET /api/v1/models/leaderboard route
status: open
---

# 009 — Implement GET /api/v1/models/leaderboard route

## Goal

`GET /api/v1/models/leaderboard` reads `leaderboard.json` from disk and
returns regression and forecast model scores as JSON, or returns 503 with a
clear message if the file does not exist yet.

## User Story

As a homeowner or reviewer, I want to call a single endpoint and see which
models were evaluated, each model's score, and which one the system is
currently using — so I can trust the predictions.

## Reference Docs

- `docs/api-contracts.md` — route conventions, HTTP error codes
- `docs/architecture.md` — `MODEL_PATH_FULL` env var and `src/model/trained/` layout

## Acceptance Criteria

- [ ] `GET /api/v1/models/leaderboard` returns HTTP 200 with a JSON body that has top-level keys `regression` and `forecast`
- [ ] Each `regression` entry has keys `model`, `r2`, `winner`
- [ ] Each `forecast` entry has keys `model`, `mape`, `winner`
- [ ] The file is read from `pathlib.Path(MODEL_PATH_FULL).parent / "leaderboard.json"`
- [ ] If `leaderboard.json` does not exist, the route raises `HTTPException(503, detail="Leaderboard not available — run training scripts first")`
- [ ] No model is loaded or retrained by calling this endpoint
- [ ] The route is registered in `src/api/routes.py` and reachable via the existing FastAPI app

## Files to Modify

- `src/api/routes.py` — add `GET /api/v1/models/leaderboard` handler

## Out of Scope

- Simple model scores — only `regression` (full) and `forecast` sections are returned
- Leaderboard history — returns current snapshot only
- Authentication
- Frontend changes (issue 010)
- API tests for this endpoint (issue 011)

## Implementation Plan

### Step 1 — routes.py: add the leaderboard endpoint

Tests live in issue 011 so the full TDD cycle closes there. This step is the implementation only.

**File:** `src/api/routes.py` — add after existing route handlers:

```python
import json
import pathlib

@router.get("/api/v1/models/leaderboard")
def get_leaderboard():
    model_path = os.environ.get("MODEL_PATH_FULL", "src/model/trained/model_full.joblib")
    leaderboard_path = pathlib.Path(model_path).parent / "leaderboard.json"
    if not leaderboard_path.exists():
        raise HTTPException(
            status_code=503,
            detail="Leaderboard not available — run training scripts first",
        )
    return json.loads(leaderboard_path.read_text())
```

Ensure `import json`, `import pathlib`, and `import os` are present at the top of `routes.py`
(add only the imports that are missing — do not touch existing imports).

## Git

- **Branch:** `feat/009-leaderboard-api-route`
- **Commit format:** `feat(api): add GET /api/v1/models/leaderboard route`
- **PR title:** `feat(api): GET /api/v1/models/leaderboard`
