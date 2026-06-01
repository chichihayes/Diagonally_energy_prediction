# AGENTS.md â€” Diagonally Energy Prediction

Same standards as CLAUDE.md. Read that file first.

## Task sequence (follow this for every issue)
1. Read the issue file fully before writing any code
2. Read every doc listed under Reference Docs
3. Create the feature branch: git checkout -b feature/NNN-slug
4. Write the failing test first â€” confirm it fails
5. Implement the minimum code to make it pass
6. Run the full test suite â€” all must pass
7. Run the self-audit checklist below
8. Commit: feat(scope): description closes #NNN
9. Push the branch

## Self-audit checklist
- [ ] Every changed line traces to the issue
- [ ] No files modified outside Files to Modify
- [ ] Tests written before implementation
- [ ] All tests pass
- [ ] No new dependencies added without explicit approval
- [ ] Error handling matches the standard (HTTPException only)
- [ ] Feature names are identical between training and inference
- [ ] Model is not retrained inside the API
- [ ] Cost calculation reads tariff from env variable — not hardcoded
- [ ] Predictions are stored in Supabase after every API call
- [ ] Scheduler errors are logged and do not crash the app
- [ ] Frontend makes fetch() calls to API only — no direct DB calls
