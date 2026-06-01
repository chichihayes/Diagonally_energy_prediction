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
