---
epic: E2-smart-home-dashboard
feature: F3
issue: 003
slug: dashboard-auto-refresh
---

# 003 — Add 15-minute client-side auto-refresh

## Goal

The dashboard silently re-fetches and re-renders all data every 15 minutes
via setInterval — updating DOM in place, with no full page reload, and
leaving existing data visible if a refresh fetch fails.

## User Story

As a Smart Home homeowner, I want my dashboard to update automatically every
15 minutes so I always see a fresh prediction without remembering to reload
the page.

## Reference Docs

- `docs/architecture.md` — APScheduler fires every 15 min writing new
  predictions to Supabase; dashboard polling interval must match this cadence
- `docs/api-contracts.md` — GET /api/v1/predictions query params; same
  endpoint used by the initial load (Issue 002)

## Acceptance Criteria

- [ ] `startAutoRefresh(intervalMs)` calls `setInterval` with `intervalMs`
      and returns the timer ID
- [ ] `startAutoRefresh(900000)` is called once, after the initial
      `loadDashboard()` call completes, on `DOMContentLoaded`
- [ ] On each timer tick, `fetchLatestPrediction()`, `populateHeroCard()`,
      `populateSensorGrid()`, and `populateWeatherStrip()` are called in
      the same order as the initial load
- [ ] The `#last-updated` element shows the `created_at` timestamp from
      the freshest API record — NOT the clock time of the browser tick
- [ ] If a refresh fetch fails, `#error-banner` appears with
      `"Auto-refresh failed. Showing last known data."` — the hero card
      and sensor grid values are NOT cleared or reset to "—"
- [ ] A successful refresh after a failed one hides `#error-banner` and
      updates all DOM slots with fresh values
- [ ] No full page reload occurs on any timer tick — verified by
      observing that a global JS variable set after the initial load
      remains intact after a tick fires

## Files to Modify

- `frontend/assets/app.js` — add `startAutoRefresh()` and a `refreshDashboard()`
  function that reuses the populate functions from Issue 002; wire both
  into the DOMContentLoaded init guard

## Out of Scope

- Server-sent events or WebSockets — client polling is sufficient per the
  feature spec
- Changing the APScheduler interval — that is fixed at 15 minutes in
  `src/services/scheduler.py`
- Prediction history table (F4)
- Per-room breakdown charts (out of scope for the whole feature)

## Implementation Plan

### Step 1 — Implement refreshDashboard() that preserves existing data on error

**Test (manual console):** After the page has loaded, set
`window.__refreshCount = 0` in the console. Manually call
`refreshDashboard()`. Confirm `window.__refreshCount` is incremented by the
function at the start of each call (add one line during development to track
this). Disconnect the network and call `refreshDashboard()` again. Confirm
the hero card still shows the previous values and the error banner text is
`"Auto-refresh failed. Showing last known data."`.

**File:** `frontend/assets/app.js`

```js
async function refreshDashboard() {
  const banner = document.getElementById('error-banner');
  try {
    const prediction = await fetchLatestPrediction();
    banner.hidden = true;
    populateHeroCard(prediction);
    populateSensorGrid(prediction.input_features);
    populateWeatherStrip(prediction.input_features);
  } catch {
    banner.textContent = 'Auto-refresh failed. Showing last known data.';
    banner.hidden = false;
    // do not clear existing DOM values — leave last known data intact
  }
}
```

### Step 2 — Implement startAutoRefresh()

**Test (manual console):** Run:

```js
let tickCount = 0;
const id = startAutoRefresh(200); // 200 ms for test speed
setTimeout(() => {
  clearInterval(id);
  console.assert(tickCount >= 2, 'Expected at least 2 ticks in 600 ms');
}, 600);
```

Then confirm the test passes. Restore the call site to `900000` ms before
committing.

**File:** `frontend/assets/app.js`

```js
function startAutoRefresh(intervalMs) {
  return setInterval(refreshDashboard, intervalMs);
}
```

### Step 3 — Wire startAutoRefresh into the DOMContentLoaded init guard

**Test (manual):** Load dashboard.html with the API running. Open DevTools
Network tab. Filter for `/api/v1/predictions`. Wait 15 minutes (or
temporarily set the interval to 5 seconds by editing the constant). Confirm
a second network request appears without any page reload and all DOM values
update.

**File:** `frontend/assets/app.js`

Replace the existing init guard from Issue 002:

```js
const REFRESH_INTERVAL_MS = 15 * 60 * 1000; // 15 minutes

if (document.getElementById('hero-card')) {
  document.addEventListener('DOMContentLoaded', async () => {
    await loadDashboard();
    startAutoRefresh(REFRESH_INTERVAL_MS);
  });
}
```

### Step 4 — Verify no page reload on tick

**Test (manual):** After page load, open the console and run:
`window.__dashboardLoaded = true`. Wait for or manually trigger one
`refreshDashboard()` call. Run `window.__dashboardLoaded` in the console.
It must still return `true` — proving the DOM update happened in place
without a full reload.

**File:** No code change — this step is a verification-only test of the
implementation from Steps 1–3.

## Git

- **Branch:** `feat/003-dashboard-auto-refresh`
- **Commit format:** `feat(frontend): add 15-minute setInterval auto-refresh to dashboard`
- **PR title:** `feat: dashboard.html 15-minute auto-refresh with preserved last-known data on error (#003)`
