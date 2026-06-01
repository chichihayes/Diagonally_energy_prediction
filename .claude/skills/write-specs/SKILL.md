---
name: write-specs
description: Generate all docs/ spec files from a confirmed PRD. Run after PRD is approved, before epics.
---

# Skill: Write Specs

From the PRD at the path provided, generate:
- docs/schema.md â€” feature schema, input/output shapes, data types
- docs/api-contracts.md â€” every route with request/response shapes
- docs/architecture.md â€” file structure, data flow, service boundaries
- docs/decisions.md â€” ADRs for every major technical choice
- docs/env.md â€” all environment variables

Mark unknowns as <!-- TODO --> placeholders.
Do not proceed to epics until the user has reviewed and approved all files.
