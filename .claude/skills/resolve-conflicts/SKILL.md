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
