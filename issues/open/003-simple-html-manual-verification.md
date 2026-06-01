---
epic: E1-instant-appliance-prediction
feature: F2
issue: 003
slug: simple-html-manual-verification
---

# 003 — Wire up and manually verify simple.html end-to-end

## Goal

A homeowner can open simple.html in a browser with the local API running, submit
a valid prediction, and see the result card — or see a clear inline error — without
any page reload at any point.

## User Story

As a homeowner, I want confidence that the form I use works correctly end-to-end
in a real browser, so I know the prediction and error paths are solid before the
app is shared.

## Reference Docs

- `docs/api-contracts.md` — POST /api/v1/predict/simple request and response
- `docs/architecture.md` — how to start the FastAPI server locally

## Acceptance Criteria

- [ ] API starts locally with `uvicorn src.api.main:app --reload` without errors
- [ ] Opening `frontend/simple.html` directly in a browser (file://) or via a local server shows the form
- [ ] Submitting `lights=100, T1=22, city=Lagos` returns a 200 and result card renders with all eight values
- [ ] Submitting with an empty city field shows an inline error beneath the city input — no page reload
- [ ] Submitting with `lights=-10` shows inline error "Lights must be 0 or greater" — no API call made
- [ ] Submitting with `T1=99` shows inline error "Temperature must be between −20 and 60 °C" — no API call made
- [ ] Submitting when the API is not running shows the inline error container with a network error message
- [ ] Browser console shows no unhandled JavaScript errors during any of the above steps

## Files to Modify

No new source files. This issue fixes bugs found during verification. If a bug is
found, the fix goes in the file it belongs to:

- `frontend/simple.html` — HTML/layout bugs
- `frontend/assets/app.js` — logic or fetch bugs
- `frontend/assets/style.css` — style bugs

## Out of Scope

- Automated browser tests (e.g. Playwright)
- Prediction history (F3)
- The full Smart Home tier form

## Implementation Plan

### Step 1 — Start the API locally

**Test:** Run `uvicorn src.api.main:app --reload`. Open `http://localhost:8000/health`.
Confirm `{ "status": "ok" }` is returned.

**File:** No file change — server start only.

```bash
uvicorn src.api.main:app --reload
```

### Step 2 — Open simple.html and test valid submission

**Test (manual, golden path):**

1. Open `simple.html` in browser (either `file://` or `http://localhost:8000/frontend/simple.html`
   if served from FastAPI static files).
2. Enter `lights = 100`, `T1 = 22`, `City = Lagos`.
3. Click "Get Prediction".

Expected outcome:
- Spinner appears on button, button disabled.
- Result card becomes visible.
- `#result-wh` contains a number followed by "Wh".
- `#result-kwh` contains a number followed by "kWh".
- `#result-cost` contains "₦" followed by a number.
- All five weather fields (`#result-t-out`, `#result-rh-out`, `#result-windspeed`,
  `#result-visibility`, `#result-tdewpoint`) show numeric values with correct units.
- Spinner clears, button re-enables.

**File:** No change if test passes.

### Step 3 — Test missing-field validation (no page reload)

**Test (manual):**

1. Clear all fields. Click "Get Prediction".
2. Confirm error appears under city input: "City is required".
3. Confirm the URL in the browser bar has NOT changed (no reload).
4. Confirm no network request was made (check DevTools → Network tab: no POST fired).

**File:** Fix `frontend/assets/app.js` if validation fires after fetch instead of before.

### Step 4 — Test out-of-range validation

**Test (manual):**

| Input | Expected inline error |
|---|---|
| lights = −10, T1 = 22, city = Lagos | "Lights must be 0 or greater" under lights input |
| lights = 100, T1 = 99, city = Lagos | "Temperature must be between −20 and 60 °C" under T1 input |

Confirm no POST is fired in either case (Network tab empty).

**File:** Fix `frontend/assets/app.js` if wrong error text is shown.

### Step 5 — Test API-down error path

**Test (manual):**

1. Stop the API server.
2. Submit a valid form.
3. Confirm `#error-container` appears with a network error message (e.g. "Failed to fetch").
4. Confirm result card remains hidden.
5. Confirm button re-enables after the error.

**File:** Fix `frontend/assets/app.js` catch block if error is swallowed silently.

### Step 6 — Check browser console for JS errors

**Test (manual):** Open DevTools Console before and after each of Steps 2–5.
Confirm zero unhandled errors or unhandled promise rejections appear.

**File:** Fix whichever file the error originates from.

## Git

- **Branch:** `feat/003-simple-html-verification`
- **Commit format:** `fix(frontend): resolve bugs found during simple.html manual verification`
- **PR title:** `fix: simple.html end-to-end verification fixes (#003)`

> If no bugs are found, this issue closes with no commit. The branch can be
> opened as a no-change PR with a verification report in the PR description.
