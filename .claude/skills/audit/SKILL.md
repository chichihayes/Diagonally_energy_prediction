---
name: audit
description: Post-implementation audit. Called automatically after implement. Checks 7 dimensions before a PR is opened.
---

# Skill: Audit

Check the diff against the issue and spec docs across 7 dimensions:
1. TDD Integrity â€” tests written before implementation?
2. Spec Compliance â€” implementation matches docs/?
3. Feature Consistency â€” feature names identical between training and inference?
4. Error Handling â€” HTTPException only, correct status codes?
5. Performance â€” model loaded once at startup, not per request?
6. Coding Standards â€” matches CLAUDE.md conventions?
7. Scope Discipline â€” only files in Files to Modify touched?

Output: PASS or FAIL with specific line references for each failure.
End with [APPROVED] if all pass, [CHANGES REQUIRED] if any fail.
