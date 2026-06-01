# setup.ps1 - bootstrap Diagonally Energy Prediction with the AI workflow scaffolding
# Usage: .\setup.ps1
# Run from inside your project folder e.g: C:\Users\HP\Desktop\programming\diagonally-energy-prediction

$APP_NAME = "Diagonally Energy Prediction"
$APP_SLUG = "diagonally-energy-prediction"
$APP_DIR = (Get-Location).Path

Write-Host ""
Write-Host "================================================"
Write-Host "   AI Workflow Setup - $APP_NAME"
Write-Host "================================================"
Write-Host ""
Write-Host "-> Creating folder structure..."

# ── Directories ──────────────────────────────────────────────
$dirs = @(
    "data/raw",
    "data/processed",
    "notebooks",
    "src/api",
    "src/model/trained",
    "src/services",
    "tests",
    "scripts",
    "docs",
    "issues/epics",
    "issues/features",
    "issues/open",
    "issues/in-progress",
    "issues/done",
    "issues/discovered",
    ".github/workflows",
    ".claude/skills/grill-me",
    ".claude/skills/write-prd",
    ".claude/skills/write-specs",
    ".claude/skills/write-system-specs",
    ".claude/skills/prd-to-epics",
    ".claude/skills/epic-to-features",
    ".claude/skills/feature-to-issues",
    ".claude/skills/plan-issues",
    ".claude/skills/implement",
    ".claude/skills/audit",
    ".claude/skills/resolve-conflicts",
    ".claude/skills/review",
    ".claude/skills/improve-architecture",
    ".claude/skills/debug",
    ".codex"
)

foreach ($dir in $dirs) {
    New-Item -ItemType Directory -Force -Path $dir | Out-Null
}

# ── CLAUDE.md ─────────────────────────────────────────────────
Write-Host "-> Writing CLAUDE.md..."
@'
# CLAUDE.md — Diagonally Energy Prediction

## What this app is
Diagonally Energy Prediction is a machine learning system that predicts electricity
consumption in real time. It ingests time-series energy data, engineers features,
trains a regression model, and exposes predictions via a REST API. The goal is to
provide accurate, low-latency electricity usage forecasts for integration into
energy management dashboards or third-party platforms.

## Stack
- Language: Python 3.11
- API: FastAPI + Uvicorn
- ML: scikit-learn (Random Forest / XGBoost)
- Data: pandas, numpy
- Model persistence: joblib
- Dataset: UCI ElectricityLoadDiagrams 2011-2014
- Testing: pytest + httpx
- CI: GitHub Actions

## Environment variables
```
MODEL_PATH=src/model/trained/model.joblib
API_HOST=0.0.0.0
API_PORT=8000
```

## Spec documents (read before touching any file)
- `docs/schema.md` — data schema, feature definitions, input/output shapes
- `docs/api-contracts.md` — every route, request shape, response shape
- `docs/architecture.md` — file structure, data flow, service boundaries
- `docs/decisions.md` — why things are built the way they are
- `docs/env.md` — environment variables reference

## Module map
```
diagonally-energy-prediction/
├── data/
│   ├── raw/                         # original UCI dataset (LD2011_2014.txt)
│   └── processed/                   # engineered features (features.csv)
├── notebooks/                       # EDA and experimentation
├── src/
│   ├── api/
│   │   ├── main.py                  # FastAPI app entry point
│   │   └── routes.py                # prediction routes
│   ├── model/
│   │   ├── train.py                 # train and save model
│   │   ├── predict.py               # load model and run inference
│   │   └── trained/                 # saved model files (gitignored)
│   └── services/
│       ├── features.py              # feature engineering pipeline
│       └── data_loader.py           # load and preprocess raw data
├── tests/
│   ├── test_api.py                  # API endpoint tests
│   ├── test_features.py             # feature engineering tests
│   └── test_model.py                # model prediction tests
├── scripts/
│   ├── download_data.py             # fetch dataset
│   └── run_training.py              # trigger model training
└── .github/workflows/
    └── ci.yml                       # run tests on push
```

## ML conventions
- Always load the model once at startup using a global singleton — never reload per request
- Feature engineering must be identical at training time and inference time
- All feature names must match exactly between train.py and predict.py
- Never pull all rows into memory for prediction — accept feature dict, return float
- Model files go in src/model/trained/ and are gitignored
- Retrain by running scripts/run_training.py — never retrain inside the API

## Naming conventions
- Files: snake_case
- Functions: snake_case
- Routes: /kebab-case
- Feature columns: snake_case

## Error handling
- Raise HTTPException with correct status code — nothing else
- 400 bad input, 422 validation error, 500 model error
- Never catch exceptions silently
- Never return 200 with an error in the body

## TDD rules
- Write the failing test first. Confirm it fails. Then implement.
- Every function that transforms data or calls the model has a test
- A test that passes before implementation exists is wrong — fix the test

## Coding standards
- Minimum code that solves the problem. Nothing speculative.
- No features beyond what was asked
- No abstractions for single-use code
- If it could be 50 lines, do not write 200
- Every changed line traces directly to the task
- Do not touch files outside the task scope
- Match existing style even if you would do it differently

## Communication style
- State assumptions before implementing
- If multiple interpretations exist, present them — do not pick silently
- If something is unclear, stop and ask
- Surface tradeoffs before choosing an approach
'@ | Set-Content -Path "CLAUDE.md" -Encoding UTF8

# ── AGENTS.md ─────────────────────────────────────────────────
Write-Host "-> Writing AGENTS.md..."
@'
# AGENTS.md — Diagonally Energy Prediction

Same standards as CLAUDE.md. Read that file first.

## Task sequence (follow this for every issue)
1. Read the issue file fully before writing any code
2. Read every doc listed under Reference Docs
3. Create the feature branch: git checkout -b feature/NNN-slug
4. Write the failing test first — confirm it fails
5. Implement the minimum code to make it pass
6. Run the full test suite — all must pass
7. Run the self-audit checklist below
8. Commit: feat(scope): description closes #NNN
9. Push the branch

## Self-audit checklist
- [ ] Every changed line traces to the issue
- [ ] No files modified outside Files to Modify
- [ ] Tests written before implementation
- [ ] All tests pass
- [ ] No new dependencies added without explicit approval
- [ ] Error handling matches the standard (HTTPException only)
- [ ] Feature names are identical between training and inference
- [ ] Model is not retrained inside the API
'@ | Set-Content -Path "AGENTS.md" -Encoding UTF8

# ── docs/ placeholder files ───────────────────────────────────
Write-Host "-> Writing docs/ placeholder files..."

@'
# docs/schema.md — Diagonally Energy Prediction
<!-- TODO: Fill after running /write-specs -->
## Feature Schema
| Feature | Type | Description |
|---|---|---|
| hour | int | Hour of day (0-23) |
| day_of_week | int | Day of week (0=Mon, 6=Sun) |
| month | int | Month (1-12) |
| is_weekend | int | 1 if Saturday or Sunday |
| lag_1h | float | Consumption 1 hour ago (kWh) |
| lag_24h | float | Consumption 24 hours ago (kWh) |
| lag_168h | float | Consumption 1 week ago (kWh) |
| rolling_mean_3h | float | Rolling mean over last 3 hours |
| rolling_mean_24h | float | Rolling mean over last 24 hours |
| target | float | Actual consumption (kWh) — label |
'@ | Set-Content -Path "docs/schema.md" -Encoding UTF8

@'
# docs/api-contracts.md — Diagonally Energy Prediction
<!-- TODO: Fill after running /write-specs -->

## POST /api/v1/predict
Request:
```json
{
  "hour": 14,
  "day_of_week": 2,
  "month": 6,
  "is_weekend": 0,
  "lag_1h": 0.45,
  "lag_24h": 0.50,
  "lag_168h": 0.48,
  "rolling_mean_3h": 0.47,
  "rolling_mean_24h": 0.49
}
```
Response:
```json
{
  "predicted_kwh": 0.512
}
```

## GET /health
Response:
```json
{ "status": "ok" }
```
'@ | Set-Content -Path "docs/api-contracts.md" -Encoding UTF8

@'
# docs/architecture.md — Diagonally Energy Prediction
<!-- TODO: Fill after running /write-specs -->

## Data Flow
raw txt file → data_loader.py → features.py → features.csv → train.py → model.joblib
                                                                              ↓
                                                           predict.py ← routes.py ← API request
'@ | Set-Content -Path "docs/architecture.md" -Encoding UTF8

@'
# docs/decisions.md — Diagonally Energy Prediction
<!-- TODO: Fill after running /write-specs -->

## ADR-001: Random Forest as baseline model
Random Forest chosen as the first model for its robustness to outliers,
no need for feature scaling, and strong performance on tabular time series.
XGBoost to be evaluated in a later sprint.

## ADR-002: joblib for model persistence
joblib is the standard for scikit-learn model serialization.
Smaller file size and faster load than pickle for numpy arrays.

## ADR-003: Features engineered offline, not in API
Feature engineering runs at training time and produces features.csv.
The API receives already-engineered features to keep inference fast and simple.
'@ | Set-Content -Path "docs/decisions.md" -Encoding UTF8

@'
# docs/env.md — Diagonally Energy Prediction

## Required environment variables

```
MODEL_PATH=src/model/trained/model.joblib
API_HOST=0.0.0.0
API_PORT=8000
```

## Where to get each
- MODEL_PATH: path to the trained model file — generated by running scripts/run_training.py
- API_HOST: host to bind the FastAPI server (default 0.0.0.0 for all interfaces)
- API_PORT: port to run the API on (default 8000)
'@ | Set-Content -Path "docs/env.md" -Encoding UTF8

# ── issues/STATUS.md ──────────────────────────────────────────
Write-Host "-> Writing issues/STATUS.md..."
@'
# Issue Status

> Auto-generated by scripts/status.sh --write

## Legend
| Icon | State | Meaning |
|---|---|---|
| 🔒 | blocked | Has blockers not yet merged |
| ⏳ | open | Ready to implement — no blockers |
| 🔨 | in-progress | Worktree running |
| ✗ | audit-failed | Audit found blocking issues |
| ✓ | audit-passed | Audit approved, branch pushed |
| 👁 | pr-open | PR open on GitHub |
| ✅ | merged | PR merged to main |
| 👤 | manual | Human-in-loop — cannot be automated |

## Issues

| # | Title | Phase | Status | Branch | Blocked by | PR | Updated |
|---|---|---|---|---|---|---|---|
| — | No issues yet | — | — | — | — | — | — |

## Last refreshed: never
'@ | Set-Content -Path "issues/STATUS.md" -Encoding UTF8

# ── issues/merge-log.md ───────────────────────────────────────
@'
# Merge Log
<!-- Append a row here each time a PR merges -->
| Issue | PR | Merged at | Notes |
|---|---|---|---|
'@ | Set-Content -Path "issues/merge-log.md" -Encoding UTF8

# ── .github/pull_request_template.md ─────────────────────────
Write-Host "-> Writing PR template..."
@'
## Issue
Closes #

## What this PR does
<!-- One sentence -->

## Checklist
- [ ] Tests written before implementation
- [ ] All tests pass
- [ ] Audit passed ([APPROVED] in audit log)
- [ ] No files modified outside scope
- [ ] Feature names consistent between training and inference
- [ ] Model not retrained inside the API
'@ | Set-Content -Path ".github/pull_request_template.md" -Encoding UTF8

# ── .github/workflows/ci.yml ──────────────────────────────────
Write-Host "-> Writing GitHub Actions CI workflow..."
@'
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: "3.11"
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests
        run: pytest tests/
'@ | Set-Content -Path ".github/workflows/ci.yml" -Encoding UTF8

# ── .env.example ──────────────────────────────────────────────
Write-Host "-> Writing .env.example..."
@'
MODEL_PATH=src/model/trained/model.joblib
API_HOST=0.0.0.0
API_PORT=8000
'@ | Set-Content -Path ".env.example" -Encoding UTF8

# ── requirements.txt ──────────────────────────────────────────
Write-Host "-> Writing requirements.txt..."
@'
fastapi
uvicorn
pandas
numpy
scikit-learn
joblib
python-dotenv
pytest
httpx
xgboost
'@ | Set-Content -Path "requirements.txt" -Encoding UTF8

# ── README.md ─────────────────────────────────────────────────
Write-Host "-> Writing README.md..."
@'
# Diagonally Energy Prediction

ML system for real-time electricity consumption prediction via REST API.

## Stack
- Model: scikit-learn (Random Forest / XGBoost)
- API: FastAPI
- Dataset: UCI ElectricityLoadDiagrams 2011-2014

## Setup
```bash
python -m venv venv
venv\Scripts\activate       # Windows
pip install -r requirements.txt
cp .env.example .env
```

## Train the model
```bash
python scripts/run_training.py
```

## Run the API
```bash
uvicorn src.api.main:app --reload
```

## Test
```bash
pytest tests/
```

## Predict (example)
```bash
curl -X POST http://localhost:8000/api/v1/predict \
  -H "Content-Type: application/json" \
  -d '{"hour":14,"day_of_week":2,"month":6,"is_weekend":0,"lag_1h":0.45,"lag_24h":0.50,"lag_168h":0.48,"rolling_mean_3h":0.47,"rolling_mean_24h":0.49}'
```
'@ | Set-Content -Path "README.md" -Encoding UTF8

# ── .gitignore ────────────────────────────────────────────────
Write-Host "-> Writing .gitignore..."
@'
.env
.env.local
__pycache__/
*.pyc
.pytest_cache/
.venv/
venv/
node_modules/
.worktrees/
data/raw/
src/model/trained/
*.joblib
*.pkl
.ipynb_checkpoints/
'@ | Set-Content -Path ".gitignore" -Encoding UTF8

# ── Skill files ───────────────────────────────────────────────
Write-Host "-> Writing skill files..."

@'
---
name: grill-me
description: Interview the user about a feature or product until full alignment is reached. Use at the start of any new PRD or feature.
---

# Skill: Grill Me

Interview the user until you have enough to write a complete PRD.

Ask one question at a time. Cover:
1. What problem does this solve and for who?
2. Who are the users and what are their roles?
3. What does success look like?
4. What is explicitly out of scope?
5. What are the technical constraints?
6. What does the happy path look like end to end?

When alignment is reached, say: "Type: write the PRD" to proceed.
'@ | Set-Content -Path ".claude/skills/grill-me/SKILL.md" -Encoding UTF8

@'
---
name: write-prd
description: Summarise a completed Grill Me alignment session into a structured PRD file.
---

# Skill: Write PRD

Write a PRD to issues/prd-[slug].md with these sections:
1. Problem Statement
2. Users and Roles
3. Solution Overview
4. Happy Path (numbered steps)
5. Out of Scope
6. Acceptance Criteria
7. Module Map (files this touches)
8. Implementation Decisions (tech choices already made)
'@ | Set-Content -Path ".claude/skills/write-prd/SKILL.md" -Encoding UTF8

@'
---
name: write-specs
description: Generate all docs/ spec files from a confirmed PRD. Run after PRD is approved, before epics.
---

# Skill: Write Specs

From the PRD at the path provided, generate:
- docs/schema.md — feature schema, input/output shapes, data types
- docs/api-contracts.md — every route with request/response shapes
- docs/architecture.md — file structure, data flow, service boundaries
- docs/decisions.md — ADRs for every major technical choice
- docs/env.md — all environment variables

Mark unknowns as <!-- TODO --> placeholders.
Do not proceed to epics until the user has reviewed and approved all files.
'@ | Set-Content -Path ".claude/skills/write-specs/SKILL.md" -Encoding UTF8

@'
---
name: write-system-specs
description: Generate behavioural specs for complex stateful systems like the training pipeline or feature engineering flow.
---

# Skill: Write System Specs

For the system described, produce docs/systems/[name].md containing:
1. State machine diagram (text-based)
2. All valid state transitions with triggers
3. What is written to disk at each transition
4. Error states and recovery paths
5. Sequence diagram for the happy path
'@ | Set-Content -Path ".claude/skills/write-system-specs/SKILL.md" -Encoding UTF8

@'
---
name: prd-to-epics
description: Break a confirmed PRD into 2-5 user-facing capability epics. Run after spec docs are locked.
---

# Skill: PRD to Epics

Read the PRD. Produce 2-5 epics in issues/epics/E[N]-[slug].md.

Rules:
- Epics are user-facing capabilities, not technical layers
- Each epic has a clear user outcome
- No "Database" or "Infrastructure" epics
- Each epic file: Goal, User Stories, Features list (2-4), Out of Scope
'@ | Set-Content -Path ".claude/skills/prd-to-epics/SKILL.md" -Encoding UTF8

@'
---
name: epic-to-features
description: Break one epic into 2-4 vertical slice features. Each feature must have a visible user output.
---

# Skill: Epic to Features

Read the epic file. Produce features in issues/features/[epic]/F[N]-[slug].md.

Rules:
- Each feature is a vertical slice (touches all layers)
- Each feature has a visible output the user can see or test
- No horizontal features (e.g. "write all the tests")
- Each feature file: Goal, User Story, Issues list (1-4), Out of Scope
'@ | Set-Content -Path ".claude/skills/epic-to-features/SKILL.md" -Encoding UTF8

@'
---
name: feature-to-issues
description: Break one feature into 1-4 atomic implementation issues with full TDD plans.
---

# Skill: Feature to Issues

Read the feature file. Produce issues in issues/open/[NNN]-[slug].md.

Each issue must contain:
- Goal (one sentence, user perspective)
- User Story
- Reference Docs (which docs/ files to read)
- Acceptance Criteria (checkboxes matching tests)
- Files to Modify (exact paths)
- Out of Scope
- Implementation Plan (Step / Test / File for each step)
- Git section (branch name, commit format, PR title)

Test assertions must be specific: function name, input, expected output.
Vague tests ("it should work") are not acceptable.
'@ | Set-Content -Path ".claude/skills/feature-to-issues/SKILL.md" -Encoding UTF8

@'
---
name: plan-issues
description: Build a DAG from all open issues, group into parallel phases, generate worktree-run.sh.
---

# Skill: Plan Issues

Read all files in issues/open/. Build a dependency graph from "Blocked by" fields.
Topological sort into phases where all issues in a phase can run in parallel.

Output:
1. issues/EXECUTION_PLAN.md — phase table + ASCII DAG
2. scripts/worktree-run.sh — executable script that runs one phase in parallel worktrees

Review with the user before confirming. A missing dependency = two conflicting issues in the same phase.
'@ | Set-Content -Path ".claude/skills/plan-issues/SKILL.md" -Encoding UTF8

@'
---
name: implement
description: Execute one issue with strict TDD. Called automatically by once.sh and worktree-run.sh.
---

# Skill: Implement

Given an issue file:
1. Read the issue fully
2. Read every doc in Reference Docs
3. For each step in Implementation Plan:
   a. Write the failing test
   b. Confirm it fails
   c. Write minimum implementation to pass
   d. Run full test suite — all must pass
4. Run self-audit checklist
5. Commit with the format in the Git section

Never write implementation before a failing test exists.
Never modify files outside Files to Modify.
Never retrain the model inside the API.
'@ | Set-Content -Path ".claude/skills/implement/SKILL.md" -Encoding UTF8

@'
---
name: audit
description: Post-implementation audit. Called automatically after implement. Checks 7 dimensions before a PR is opened.
---

# Skill: Audit

Check the diff against the issue and spec docs across 7 dimensions:
1. TDD Integrity — tests written before implementation?
2. Spec Compliance — implementation matches docs/?
3. Feature Consistency — feature names identical between training and inference?
4. Error Handling — HTTPException only, correct status codes?
5. Performance — model loaded once at startup, not per request?
6. Coding Standards — matches CLAUDE.md conventions?
7. Scope Discipline — only files in Files to Modify touched?

Output: PASS or FAIL with specific line references for each failure.
End with [APPROVED] if all pass, [CHANGES REQUIRED] if any fail.
'@ | Set-Content -Path ".claude/skills/audit/SKILL.md" -Encoding UTF8

@'
---
name: resolve-conflicts
description: Auto-resolve merge conflicts when a feature branch collides with newer main. Called automatically by worktree-run.sh.
---

# Skill: Resolve Conflicts

When a merge conflict is detected:
1. Read the conflicting sections
2. Read the relevant spec doc as ground truth
3. If the resolution is unambiguous (spec clearly says one way): resolve and continue
4. If ambiguous (same-line edit, spec-doc divergence): output [ESCALATE: file:reason] and stop

Never guess on ambiguous conflicts. Escalate to the human.
'@ | Set-Content -Path ".claude/skills/resolve-conflicts/SKILL.md" -Encoding UTF8

@'
---
name: review
description: Human-facing code review on a git diff. Pipe a diff in for a structured review before merging.
---

# Skill: Review

Given a git diff, produce a structured review covering:
1. Correctness — does it do what the issue says?
2. Test coverage — are edge cases tested?
3. Feature consistency — are feature names the same as in training?
4. Readability — would a new team member understand this?
5. Spec alignment — does it match docs/?

End with: APPROVE, REQUEST CHANGES, or DISCUSS with specific items for each.
'@ | Set-Content -Path ".claude/skills/review/SKILL.md" -Encoding UTF8

@'
---
name: improve-architecture
description: Quarterly codebase health check. Identifies deep module opportunities, coupling issues, and dead code.
---

# Skill: Improve Architecture

Review the current codebase structure and produce:
1. Coupling issues — which modules know too much about each other?
2. Deep module opportunities — where can an interface hide complexity?
3. Dead code — what can be removed?
4. Test gaps — what is untested that matters?
5. Recommended refactors — ranked by impact vs effort

Produce a new issue file for each recommended refactor above the threshold.
'@ | Set-Content -Path ".claude/skills/improve-architecture/SKILL.md" -Encoding UTF8

@'
---
name: debug
description: Diagnose a stuck issue. Use when the agent is looping, failing tests it cannot fix, or hitting an unexpected error.
---

# Skill: Debug

Given the stuck state:
1. State what you expected to happen
2. State what actually happened (exact error or symptom)
3. List what you have already tried
4. Identify the smallest possible reproducing case
5. Check if the issue is in the test, the implementation, or the spec

Produce a diagnosis and a specific next action. Do not guess — if uncertain, ask.
'@ | Set-Content -Path ".claude/skills/debug/SKILL.md" -Encoding UTF8

# ── Codex symlink (Windows junction) ──────────────────────────
Write-Host "-> Creating .codex/skills junction..."
$target = (Resolve-Path ".claude/skills").Path
$junction = (Join-Path (Get-Location) ".codex/skills")
if (Test-Path $junction) { Remove-Item $junction -Recurse -Force }
cmd /c "mklink /D `"$junction`" `"$target`"" | Out-Null

# ── .gitkeep files ────────────────────────────────────────────
"" | Set-Content "data/raw/.gitkeep"
"" | Set-Content "data/processed/.gitkeep"
"" | Set-Content "notebooks/.gitkeep"
"" | Set-Content "src/model/trained/.gitkeep"
"" | Set-Content "issues/epics/.gitkeep"
"" | Set-Content "issues/features/.gitkeep"
"" | Set-Content "issues/open/.gitkeep"
"" | Set-Content "issues/in-progress/.gitkeep"
"" | Set-Content "issues/done/.gitkeep"
"" | Set-Content "issues/discovered/.gitkeep"

# ── Done ─────────────────────────────────────────────────────
Write-Host ""
Write-Host "================================================"
Write-Host "   Setup complete - $APP_NAME"
Write-Host "================================================"
Write-Host ""
Write-Host "   Created:"
Write-Host "   CLAUDE.md + AGENTS.md"
Write-Host "   README.md + requirements.txt"
Write-Host "   .env.example + .gitignore"
Write-Host "   docs/ - 5 spec placeholder files"
Write-Host "   data/raw + data/processed + notebooks/"
Write-Host "   src/api + src/model + src/services"
Write-Host "   tests/ + scripts/"
Write-Host "   issues/ - full hierarchy + STATUS.md"
Write-Host "   .github/workflows/ci.yml"
Write-Host "   .claude/skills/ - 13 skills"
Write-Host "   .codex/skills linked to .claude/skills"
Write-Host ""
Write-Host "   Next steps:"
Write-Host "   1. cd into your project folder"
Write-Host "   2. git init"
Write-Host "   3. gh repo create diagonally-energy-prediction --public --source=. --remote=origin"
Write-Host "   4. git add . && git commit -m 'chore: initial scaffold'"
Write-Host "   5. git push -u origin main"
Write-Host "   6. Open Claude Code: claude"
Write-Host "   7. Type /grill-me to start Phase 1"
Write-Host ""
