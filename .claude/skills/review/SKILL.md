---
name: review
description: Human-facing code review on a git diff. Pipe a diff in for a structured review before merging.
---

# Skill: Review

Given a git diff, produce a structured review covering:
1. Correctness â€” does it do what the issue says?
2. Test coverage â€” are edge cases tested?
3. Feature consistency â€” are feature names the same as in training?
4. Readability â€” would a new team member understand this?
5. Spec alignment â€” does it match docs/?

End with: APPROVE, REQUEST CHANGES, or DISCUSS with specific items for each.
