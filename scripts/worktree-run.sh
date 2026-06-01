#!/usr/bin/env bash
# worktree-run.sh — run one phase of the execution plan in parallel git worktrees.
#
# Usage:  ./scripts/worktree-run.sh <phase>
# Phases: 1-15  (see issues/EXECUTION_PLAN.md for the full phase table)
#
# What it does:
#   1. Creates one git worktree per issue in the phase (branch: feat/<slug>).
#   2. Launches `claude` in each worktree to implement the issue.
#   3. Waits for all agents to finish.
#   4. Reports success/failure and lists the worktree paths.
#
# After all branches are reviewed and merged to main, run the next phase.

set -euo pipefail

PHASE="${1:-}"

if [[ -z "$PHASE" ]]; then
    echo "Usage: $0 <phase-number>   (1–15)" >&2
    echo "See issues/EXECUTION_PLAN.md for the full phase table." >&2
    exit 1
fi

ROOT="$(git rev-parse --show-toplevel)"
WORKTREE_DIR="$ROOT/.worktrees"
mkdir -p "$WORKTREE_DIR"

# ── phase definitions ────────────────────────────────────────────────────────
# Each entry is a space-separated list of issue slugs (matching issues/open/*.md).

declare -a PHASE_ISSUES

case "$PHASE" in
1)
    PHASE_ISSUES=(
        "001-train-model-simple"
        "001-simple-html-form"
        "001-get-predictions-db-function"
        "001-dashboard-html-structure"
    )
    ;;
2)
    PHASE_ISSUES=(
        "002-implement-weather-client"
        "002-app-js-fetch-and-result-card"
        "002-get-predictions-api-route"
        "002-dashboard-fetch"
    )
    ;;
3)
    PHASE_ISSUES=(
        "003-implement-predict-simple-endpoint"
        "003-prediction-history-table-simple-html"
        "003-simple-html-manual-verification"
        "003-dashboard-auto-refresh"
    )
    ;;
4)
    PHASE_ISSUES=(
        "004-write-predict-simple-tests"
    )
    ;;
5)
    PHASE_ISSUES=(
        "005-train-model-full"
        "005-predictions-since-param"
        "005-implement-scheduler-submit-reading"
    )
    ;;
6)
    PHASE_ISSUES=(
        "006-implement-predict-full-endpoint"
        "006-dashboard-sparkline-chart"
        "006-wire-scheduler-into-main"
    )
    ;;
7)
    PHASE_ISSUES=(
        "007-dashboard-history-table"
        "007-write-predict-full-tests"
        "007-write-scheduler-tests"
    )
    ;;
8)
    PHASE_ISSUES=(
        "008-train-model-forecast"
        "008-forecast-html-structure"
        "008-persist-leaderboard-scores"
        "008-implement-forecast-7d-function"
    )
    ;;
9)
    PHASE_ISSUES=(
        "009-implement-forecast-py"
        "009-forecast-24h-area-chart"
        "009-implement-project-monthly-bill"
        "009-leaderboard-api-route"
    )
    ;;
10)
    PHASE_ISSUES=(
        "010-implement-forecast-24h-endpoint"
        "010-implement-forecast-7d-route"
        "010-forecast-7d-bar-chart-and-bill-card"
        "010-forecast-html-leaderboard"
    )
    ;;
11)
    PHASE_ISSUES=(
        "011-write-forecast-24h-tests"
        "011-write-forecast-7d-tests"
        "011-write-leaderboard-api-tests"
    )
    ;;
12)
    PHASE_ISSUES=(
        "012-save-training-stats-json"
        "012-implement-check-drift-function"
        "012-implement-should-retrain-condition-check"
    )
    ;;
13)
    PHASE_ISSUES=(
        "013-implement-monitor"
        "013-create-drift-log-schema-and-db-functions"
        "013-implement-run-retraining-script"
    )
    ;;
14)
    PHASE_ISSUES=(
        "014-store-anomaly-db"
        "014-wire-drift-check-into-scheduler"
        "014-wire-retrain-log-and-model-replacement"
    )
    ;;
15)
    PHASE_ISSUES=(
        "015-low-confidence-flag-api"
        "015-add-get-monitor-drift-endpoint"
        "015-add-retrain-status-api-endpoint"
    )
    ;;
*)
    echo "Unknown phase: $PHASE  (valid: 1–15)" >&2
    exit 1
    ;;
esac

echo "═══════════════════════════════════════════════════"
echo "  Phase $PHASE — ${#PHASE_ISSUES[@]} issue(s)"
echo "═══════════════════════════════════════════════════"
echo ""

# ── create worktrees and launch agents ───────────────────────────────────────
PIDS=()
declare -a WT_PATHS=()

for ISSUE in "${PHASE_ISSUES[@]}"; do
    BRANCH="feat/${ISSUE}"
    WT_PATH="$WORKTREE_DIR/$ISSUE"
    ISSUE_FILE="$ROOT/issues/open/${ISSUE}.md"

    if [[ ! -f "$ISSUE_FILE" ]]; then
        echo "✗  Issue file not found: $ISSUE_FILE" >&2
        exit 1
    fi

    if [[ -d "$WT_PATH" ]]; then
        echo "↩  Reusing worktree: $WT_PATH  (branch: $BRANCH)"
    else
        git worktree add -b "$BRANCH" "$WT_PATH" main
        echo "✚  Created worktree:  $WT_PATH  (branch: $BRANCH)"
    fi

    WT_PATHS+=("$WT_PATH")

    # Launch claude in each worktree to implement the issue.
    # Output is tee-d to .claude-log.txt inside the worktree for review.
    (
        cd "$WT_PATH"
        echo "[$(date +%T)] ▶  $ISSUE — starting"
        claude --print "$(cat "$ISSUE_FILE")" 2>&1 | tee ".claude-log.txt"
        EXIT_CODE="${PIPESTATUS[0]}"
        echo "[$(date +%T)] $([ "$EXIT_CODE" -eq 0 ] && echo '✓' || echo '✗')  $ISSUE — exit $EXIT_CODE"
        exit "$EXIT_CODE"
    ) &
    PIDS+=($!)
done

echo ""
echo "Waiting for ${#PIDS[@]} agent(s) to complete..."
echo ""

# ── collect results ───────────────────────────────────────────────────────────
FAILED=0
FAILED_ISSUES=()

for i in "${!PIDS[@]}"; do
    ISSUE="${PHASE_ISSUES[$i]}"
    if ! wait "${PIDS[$i]}"; then
        FAILED=$((FAILED + 1))
        FAILED_ISSUES+=("$ISSUE")
    fi
done

echo ""
echo "═══════════════════════════════════════════════════"

if [[ $FAILED -gt 0 ]]; then
    echo "  Phase $PHASE — FAILED ($FAILED / ${#PHASE_ISSUES[@]} issues)"
    echo ""
    for ISSUE in "${FAILED_ISSUES[@]}"; do
        echo "  ✗  $ISSUE"
        echo "     log: $WORKTREE_DIR/$ISSUE/.claude-log.txt"
    done
    echo "═══════════════════════════════════════════════════"
    exit 1
fi

echo "  Phase $PHASE — COMPLETE (${#PHASE_ISSUES[@]} / ${#PHASE_ISSUES[@]} issues)"
echo "═══════════════════════════════════════════════════"
echo ""
echo "Worktree paths:"
for WT in "${WT_PATHS[@]}"; do
    echo "  $WT"
done

echo ""
echo "Next steps:"
echo "  1. Review each worktree branch (git diff main feat/<slug>)"
echo "  2. Run tests in each worktree (pytest / open browser)"
echo "  3. Merge approved branches to main"

NEXT=$((PHASE + 1))
if [[ $NEXT -le 15 ]]; then
    echo "  4. Run the next phase:  $0 $NEXT"
    echo ""
    # E3 / E5 parallelism hint
    if [[ "$PHASE" -eq 7 ]]; then
        echo "  Tip: Phase 8 (E3 Forecast) and Phase 12 (E5 Monitoring) are independent."
        echo "       You can run them concurrently:"
        echo "         $0 8 &"
        echo "         $0 12 &"
        echo "         wait"
    fi
else
    echo ""
    echo "  All 15 phases complete."
fi
