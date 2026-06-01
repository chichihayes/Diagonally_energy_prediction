# Execution Plan — Diagonally Energy Prediction

Generated: 2026-06-01  
Total issues: 48  Total phases: 15

---

## How to read this plan

Each phase is a **parallel gate**: every issue inside a phase can be worked in a
separate git worktree simultaneously. A phase only starts when all issues in the
previous phase are merged to `main`.

Issue numbering is the canonical phase indicator — all `001-*` issues are Phase 1,
all `002-*` are Phase 2, and so on. Within a phase, issues from different epics
have no shared files and can be implemented concurrently without merge conflicts.

**Explicit `Blocked by` edges** (hard deps captured in issue frontmatter):

| Dependent | Blocked by |
|-----------|-----------|
| `002-get-predictions-api-route` | `001-get-predictions-db-function` |
| `003-prediction-history-table-simple-html` | `002-get-predictions-api-route` |
| `005-predictions-since-param` | `002-get-predictions-api-route`, `001-get-predictions-db-function` |
| `006-dashboard-sparkline-chart` | `005-predictions-since-param` |
| `007-dashboard-history-table` | `006-dashboard-sparkline-chart` |
| `013-implement-monitor` | `012-save-training-stats-json` |
| `015-low-confidence-flag-api` | `013-implement-monitor`, `014-store-anomaly-db` |

All explicit edges are satisfied by the phase ordering below.

---

## Phase table

| Phase | Step | Epic | Issues (all parallel) | Hard dep satisfied |
|-------|------|------|-----------------------|--------------------|
| **1** | 001 | E1+E2 | `001-train-model-simple` · `001-simple-html-form` · `001-get-predictions-db-function` · `001-dashboard-html-structure` | — |
| **2** | 002 | E1+E2 | `002-implement-weather-client` · `002-app-js-fetch-and-result-card` · `002-get-predictions-api-route` · `002-dashboard-fetch` | `002-get-predictions-api-route` ← P1 ✓ |
| **3** | 003 | E1+E2 | `003-implement-predict-simple-endpoint` · `003-prediction-history-table-simple-html` · `003-simple-html-manual-verification` · `003-dashboard-auto-refresh` | `003-prediction-history-table` ← P2 ✓ |
| **4** | 004 | E1 | `004-write-predict-simple-tests` | — |
| **5** | 005 | E1+E2 | `005-train-model-full` · `005-predictions-since-param` · `005-implement-scheduler-submit-reading` | `005-predictions-since-param` ← P2 ✓ |
| **6** | 006 | E2 | `006-implement-predict-full-endpoint` · `006-dashboard-sparkline-chart` · `006-wire-scheduler-into-main` | `006-dashboard-sparkline-chart` ← P5 ✓ |
| **7** | 007 | E2 | `007-dashboard-history-table` · `007-write-predict-full-tests` · `007-write-scheduler-tests` | `007-dashboard-history-table` ← P6 ✓ |
| **8** | 008 | E3 | `008-train-model-forecast` · `008-forecast-html-structure` · `008-persist-leaderboard-scores` · `008-implement-forecast-7d-function` | — |
| **9** | 009 | E3 | `009-implement-forecast-py` · `009-forecast-24h-area-chart` · `009-implement-project-monthly-bill` · `009-leaderboard-api-route` | — |
| **10** | 010 | E3 | `010-implement-forecast-24h-endpoint` · `010-implement-forecast-7d-route` · `010-forecast-7d-bar-chart-and-bill-card` · `010-forecast-html-leaderboard` | — |
| **11** | 011 | E3 | `011-write-forecast-24h-tests` · `011-write-forecast-7d-tests` · `011-write-leaderboard-api-tests` | — |
| **12** | 012 | E5 | `012-save-training-stats-json` · `012-implement-check-drift-function` · `012-implement-should-retrain-condition-check` | — |
| **13** | 013 | E5 | `013-implement-monitor` · `013-create-drift-log-schema-and-db-functions` · `013-implement-run-retraining-script` | `013-implement-monitor` ← P12 ✓ |
| **14** | 014 | E5 | `014-store-anomaly-db` · `014-wire-drift-check-into-scheduler` · `014-wire-retrain-log-and-model-replacement` | — |
| **15** | 015 | E5 | `015-low-confidence-flag-api` · `015-add-get-monitor-drift-endpoint` · `015-add-retrain-status-api-endpoint` | `015-low-confidence-flag-api` ← P13 + P14 ✓ |

---

## Parallelism opportunity — E3 and E5

Phases 8–11 (E3 Forecast) and phases 12–15 (E5 Monitoring) have **no cross-epic
dependencies** between them. Once Phase 7 is merged, both tracks can run in parallel:

```
P7 complete
    │
    ├──▶ P8 (E3) ──▶ P9 ──▶ P10 ──▶ P11
    │
    └──▶ P12 (E5) ──▶ P13 ──▶ P14 ──▶ P15
```

This reduces the critical path from 15 sequential phases to **11 phases** (7 + 4).

Note: `015-low-confidence-flag-api` modifies `routes.py` which is created by E1 P3 and
extended by E2 P6 — both complete well before E5 begins.

---

## ASCII dependency graph

Only issues with explicit `Blocked by` edges are shown. Issues without an arrow
are unblocked by their phase number alone.

```
 P1  ┌─────────────────────────────────────────────┐
     │ 001-get-predictions-db-function             │
     │ 001-train-model-simple                      │ (all parallel)
     │ 001-simple-html-form                        │
     │ 001-dashboard-html-structure                │
     └──────────┬──────────────────────────────────┘
                │
                ▼ (hard dep)
 P2  ┌──────────────────────────────────────────────┐
     │ 002-get-predictions-api-route ◀── (P1 dep)  │
     │ 002-implement-weather-client                │ (all parallel)
     │ 002-app-js-fetch-and-result-card            │
     │ 002-dashboard-fetch                         │
     └──────────┬─────────────────────┬────────────┘
                │                     │
                ▼ (hard dep)          ▼ (hard dep via same source)
 P3  ┌──────────────────┐    ┌────────────────────────────────┐
     │ 003-prediction-  │    │ 003-implement-predict-simple   │
     │ history-table ◀──┘    │ 003-simple-html-manual-verify  │
     │ (blocked by P2)  │    │ 003-dashboard-auto-refresh     │
     └──────────────────┘    └────────────────────────────────┘

     [P4 — write-predict-simple-tests — no hard dep]

                ┌──────────────────── (hard dep: 002-get-predictions-api-route, P2)
                ▼
 P5  ┌──────────────────────────────────────┐
     │ 005-predictions-since-param ◀──────  │
     │ 005-train-model-full                 │ (all parallel)
     │ 005-implement-scheduler-submit       │
     └──────────┬───────────────────────────┘
                │
                ▼ (hard dep)
 P6  ┌──────────────────────────────────────┐
     │ 006-dashboard-sparkline-chart ◀───── │
     │ 006-implement-predict-full-endpoint  │ (all parallel)
     │ 006-wire-scheduler-into-main         │
     └──────────┬───────────────────────────┘
                │
                ▼ (hard dep)
 P7  ┌──────────────────────────────────────┐
     │ 007-dashboard-history-table ◀─────── │
     │ 007-write-predict-full-tests         │ (all parallel)
     │ 007-write-scheduler-tests            │
     └──────────┬───────────────────────────┘
                │
        ┌───────┴────────┐
        ▼                ▼
   E3 track           E5 track
 P8–P11 (4 steps)   P12–P15 (4 steps)
 (all unblocked      012-save-training-stats-json
  within E3)              │
                          ▼ (hard dep)
                     013-implement-monitor
                          │
                          ▼ (hard dep, plus 014-store-anomaly-db)
                     015-low-confidence-flag-api
```

---

## Issue count per phase

```
Phase  1 │████████  4
Phase  2 │████████  4
Phase  3 │████████  4
Phase  4 │██        1
Phase  5 │██████    3
Phase  6 │██████    3
Phase  7 │██████    3
Phase  8 │████████  4
Phase  9 │████████  4
Phase 10 │████████  4
Phase 11 │██████    3
Phase 12 │██████    3
Phase 13 │██████    3
Phase 14 │██████    3
Phase 15 │██████    3
         └────────────
         Total: 48
```

---

## Running a phase

```bash
# Run all issues in phase N in parallel worktrees:
./scripts/worktree-run.sh <N>

# Example — start the project:
./scripts/worktree-run.sh 1

# After reviewing and merging all phase-1 branches to main:
./scripts/worktree-run.sh 2
```

See `scripts/worktree-run.sh` for full usage.
