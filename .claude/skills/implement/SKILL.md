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
   d. Run full test suite â€” all must pass
4. Run self-audit checklist
5. Commit with the format in the Git section

Never write implementation before a failing test exists.
Never modify files outside Files to Modify.
Never retrain the model inside the API.
