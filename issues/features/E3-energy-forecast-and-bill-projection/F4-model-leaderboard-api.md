---
epic: E3-energy-forecast-and-bill-projection
feature: F4
slug: model-leaderboard-api
---

# F4 — GET /api/v1/models/leaderboard API

## Goal

The leaderboard endpoint exists and returns R² scores for all 6 regression
models and MAPE scores for all 5 time series models, with the winner flagged
in each group. Scores are written to a JSON file during training and read back
at runtime — no retraining is triggered by the API call.

## User Story

As a homeowner or reviewer, I want to see which models were evaluated, how each
one scored, and which one the system is actually using — so I can trust the
predictions and understand the system's accuracy at a glance.

## Issues

1. **Persist leaderboard scores during training** — Update
   scripts/run_training_full.py, run_training_simple.py, and
   run_training_forecast.py to write their evaluation results to
   src/model/trained/leaderboard.json after each training run. Format: two
   top-level keys — `regression` (list of {model, r2, winner}) and `forecast`
   (list of {model, mape, winner}). The winner entry has winner=true; all
   others have winner=false.

2. **Implement GET /api/v1/models/leaderboard route** — Read
   leaderboard.json from MODEL_PATH_FULL's parent directory at request time.
   Return the JSON as-is. Return 503 with a clear message if the file does not
   exist (models not yet trained).

3. **Surface leaderboard on forecast.html** — Add a collapsible "Model
   performance" section below the bill projection card. On page load, fetch
   GET /api/v1/models/leaderboard and render two small tables: regression
   models sorted by R² descending (winner row bold), forecast models sorted by
   MAPE ascending (winner row bold). Hide the section if the endpoint returns
   503.

4. **Write tests** — test_api.py: endpoint returns 200 with regression and
   forecast keys when leaderboard.json exists; returns 503 when the file is
   absent. Assert winner=true appears exactly once in each group.

## Out of Scope

- Triggering retraining from the API — training is always offline only
- Storing leaderboard history — one current snapshot only
- regression_simple leaderboard — only regression_full and forecast are
  returned for brevity
