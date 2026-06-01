---
name: plan-issues
description: Build a DAG from all open issues, group into parallel phases, generate worktree-run.sh.
---

# Skill: Plan Issues

Read all files in issues/open/. Build a dependency graph from "Blocked by" fields.
Topological sort into phases where all issues in a phase can run in parallel.

Output:
1. issues/EXECUTION_PLAN.md â€” phase table + ASCII DAG
2. scripts/worktree-run.sh â€” executable script that runs one phase in parallel worktrees

Review with the user before confirming. A missing dependency = two conflicting issues in the same phase.
