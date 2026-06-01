---
epic: E2-smart-home-dashboard
feature: F3
issue: 002
slug: dashboard-fetch
---

# 002 — Implement app.js dashboard fetch

## Goal

On page load, the dashboard calls GET /api/v1/predictions?tier=full&limit=1,
extracts the prediction values and sensor snapshot from the response, and
populates every DOM slot — with a loading skeleton during the request and an
error banner if the fetch fails.

## User Story

As a Smart Home homeowner, I want my dashboard to automatically fill in my
latest predicted consumption, room temperatures, and outside weather as soon
as the page loads, so I never have to navigate anywhere or press a button.

## Reference Docs

- `docs/api-contracts.md` — GET /api/v1/predictions query params and response
  shape; confirms `tier`, `limit` params and the fields returned
- `docs/architecture.md` — frontend/assets/app.js owns all fetch() calls;
  routes.py is the only file that returns prediction records from Supabase

## Acceptance Criteria

- [ ] GET /api/v1/predictions?tier=full&limit=1 response includes an
      `input_features` object containing T1–T9, RH_1–RH_9, T_out, RH_out,
      Windspeed, Visibility, Tdewpoint for tier=full records
- [ ] `fetchLatestPrediction()` calls the correct URL and returns the first
      element of the response array (or `null` if the array is empty)
- [ ] `populateHeroCard({ predicted_wh: 84.3, predicted_kwh: 0.0843, estimated_cost_ngn: 7.21, created_at: '2026-06-01T10:00:00Z' })` sets `#predicted-wh` to `"84.3"`, `#predicted-kwh` to `"0.0843"`, `#estimated-cost` to `"₦7.21"`, and `#last-updated` to a non-empty, human-readable datetime string
- [ ] `populateSensorGrid({ T1: 19.89, RH_1: 47.6, T2: 19.2, RH_2: 44.79, T3: 19.79, RH_3: 44.73, T4: 17.17, RH_4: 41.67, T5: 17.2, RH_5: 55.2, T6: 7.03, RH_6: 84.26, T7: 17.2, RH_7: 41.63, T8: 18.2, RH_8: 48.9, T9: 17.03, RH_9: 45.53 })` sets `[data-room="1"] .room-temp` to `"19.89"` and `[data-room="1"] .room-humidity` to `"47.6"`
- [ ] `populateWeatherStrip({ T_out: 28.4, RH_out: 82.0, Windspeed: 3.1, Visibility: 10.0, Tdewpoint: 25.1 })` sets `#w-t-out` to `"28.4"`, `#w-rh-out` to `"82.0"`, `#w-windspeed` to `"3.1"`, `#w-visibility` to `"10.0"`, `#w-tdewpoint` to `"25.1"`
- [ ] Loading skeleton (class `animate-pulse` on the hero card) is shown while
      fetch is in flight and removed as soon as data is painted
- [ ] If the fetch returns a non-2xx status, `#error-banner` becomes visible
      with text `"Failed to load dashboard data. Please try again."`
- [ ] If the fetch returns an empty array, `#error-banner` shows
      `"No predictions found. Wait for the next scheduled reading."`

## Files to Modify

- `src/api/routes.py` — add `input_features` to the GET /api/v1/predictions
  response object for tier=full records
- `frontend/assets/app.js` — add `fetchLatestPrediction()`,
  `populateHeroCard()`, `populateSensorGrid()`, `populateWeatherStrip()`,
  `showSkeleton()`, `hideSkeleton()`, `showError()` functions; call
  `fetchLatestPrediction()` on DOMContentLoaded from a dashboard-specific
  init guard
- `frontend/dashboard.html` — add `id="error-banner"` element (hidden by
  default) and loading skeleton markup on the hero card

## Out of Scope

- Auto-refresh timer (Issue 003)
- Writing or modifying prediction records — this issue is read-only
- Displaying prediction history table (F4)
- Modifying the Supabase schema — input_features is already stored as JSONB

## Implementation Plan

### Step 1 — Add input_features to GET /api/v1/predictions response

**Assumption:** The `predictions` Supabase table already stores `input_features`
as a JSONB column (confirmed in CLAUDE.md). The route currently selects all
columns — it must explicitly include `input_features` in the serialised
response object for tier=full records.

**Test:** In `tests/test_api.py`, add:

```python
def test_get_predictions_full_tier_includes_input_features(client, seed_full_prediction):
    resp = client.get("/api/v1/predictions?tier=full&limit=1")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 1
    record = body[0]
    assert "input_features" in record
    assert "T1" in record["input_features"]
    assert "RH_1" in record["input_features"]
    assert "T_out" in record["input_features"]
```

**File:** `src/api/routes.py` — update the response model or the serialisation
logic for GET /api/v1/predictions so that each returned object includes
`input_features` when the tier is `full`.

### Step 2 — Add error banner and skeleton markup to dashboard.html

**Test (manual):** Load dashboard.html. Run in console:
`document.getElementById('error-banner').hidden` → must return `true`.
Confirm `#hero-card` has class `animate-pulse` before JS fires.

**File:** `frontend/dashboard.html`

```html
<!-- error banner — hidden until a fetch failure occurs -->
<div id="error-banner" hidden
     class="max-w-2xl mx-auto mb-4 bg-red-50 border border-red-200
            text-red-700 rounded-xl p-4 text-sm">
</div>

<!-- hero card with skeleton pulse on each slot -->
<section id="hero-card" class="max-w-2xl mx-auto bg-white rounded-2xl
         shadow p-6 mb-6 animate-pulse">
  ...
</section>
```

### Step 3 — Implement fetchLatestPrediction() in app.js

**Test (manual / DevTools Network tab):** Load dashboard.html with the API
running. Open Network tab. Confirm one request to
`/api/v1/predictions?tier=full&limit=1` is made on page load and returns 200.

**File:** `frontend/assets/app.js`

```js
async function fetchLatestPrediction() {
  const resp = await fetch('/api/v1/predictions?tier=full&limit=1');
  if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
  const data = await resp.json();
  if (data.length === 0) throw new Error('empty');
  return data[0];
}
```

### Step 4 — Implement populateHeroCard()

**Test (manual console):**

```js
populateHeroCard({
  predicted_wh: 84.3,
  predicted_kwh: 0.0843,
  estimated_cost_ngn: 7.21,
  created_at: '2026-06-01T10:00:00Z'
});
// then assert:
console.assert(document.getElementById('predicted-wh').textContent === '84.3');
console.assert(document.getElementById('predicted-kwh').textContent === '0.0843');
console.assert(document.getElementById('estimated-cost').textContent === '₦7.21');
console.assert(document.getElementById('last-updated').textContent !== '—');
```

**File:** `frontend/assets/app.js`

```js
function populateHeroCard(prediction) {
  document.getElementById('predicted-wh').textContent = prediction.predicted_wh;
  document.getElementById('predicted-kwh').textContent = prediction.predicted_kwh;
  document.getElementById('estimated-cost').textContent =
    '₦' + prediction.estimated_cost_ngn.toFixed(2);
  document.getElementById('last-updated').textContent =
    new Date(prediction.created_at).toLocaleString();
}
```

### Step 5 — Implement populateSensorGrid()

**Test (manual console):**

```js
populateSensorGrid({
  T1: 19.89, RH_1: 47.6,
  T2: 19.2,  RH_2: 44.79,
  T3: 19.79, RH_3: 44.73,
  T4: 17.17, RH_4: 41.67,
  T5: 17.2,  RH_5: 55.2,
  T6: 7.03,  RH_6: 84.26,
  T7: 17.2,  RH_7: 41.63,
  T8: 18.2,  RH_8: 48.9,
  T9: 17.03, RH_9: 45.53
});
console.assert(
  document.querySelector('[data-room="3"] .room-temp').textContent === '19.79'
);
console.assert(
  document.querySelector('[data-room="6"] .room-humidity').textContent === '84.26'
);
```

**File:** `frontend/assets/app.js`

```js
function populateSensorGrid(features) {
  for (let i = 1; i <= 9; i++) {
    const tile = document.querySelector(`[data-room="${i}"]`);
    if (!tile) continue;
    tile.querySelector('.room-temp').textContent = features[`T${i}`];
    tile.querySelector('.room-humidity').textContent = features[`RH_${i}`];
  }
}
```

### Step 6 — Implement populateWeatherStrip()

**Test (manual console):**

```js
populateWeatherStrip({ T_out: 28.4, RH_out: 82.0, Windspeed: 3.1,
                       Visibility: 10.0, Tdewpoint: 25.1 });
console.assert(document.getElementById('w-t-out').textContent === '28.4');
console.assert(document.getElementById('w-windspeed').textContent === '3.1');
```

**File:** `frontend/assets/app.js`

```js
function populateWeatherStrip(f) {
  document.getElementById('w-t-out').textContent     = f.T_out;
  document.getElementById('w-rh-out').textContent    = f.RH_out;
  document.getElementById('w-windspeed').textContent = f.Windspeed;
  document.getElementById('w-visibility').textContent = f.Visibility;
  document.getElementById('w-tdewpoint').textContent = f.Tdewpoint;
}
```

### Step 7 — Implement skeleton, error states and DOMContentLoaded init

**Test (manual):** Disconnect network. Reload dashboard.html. Confirm error
banner appears with text "Failed to load dashboard data. Please try again."
and hero card dashes remain (no stale data shown).

**File:** `frontend/assets/app.js`

```js
function showSkeleton() {
  document.getElementById('hero-card').classList.add('animate-pulse');
}
function hideSkeleton() {
  document.getElementById('hero-card').classList.remove('animate-pulse');
}
function showError(message) {
  const banner = document.getElementById('error-banner');
  banner.textContent = message;
  banner.hidden = false;
}

async function loadDashboard() {
  showSkeleton();
  try {
    const prediction = await fetchLatestPrediction();
    populateHeroCard(prediction);
    populateSensorGrid(prediction.input_features);
    populateWeatherStrip(prediction.input_features);
  } catch (err) {
    const msg = err.message === 'empty'
      ? 'No predictions found. Wait for the next scheduled reading.'
      : 'Failed to load dashboard data. Please try again.';
    showError(msg);
  } finally {
    hideSkeleton();
  }
}

// guard: only run on dashboard.html
if (document.getElementById('hero-card')) {
  document.addEventListener('DOMContentLoaded', loadDashboard);
}
```

## Git

- **Branch:** `feat/002-dashboard-fetch`
- **Commit format:** `feat(frontend): implement dashboard fetch — hero card, sensor grid, weather strip, error states`
- **PR title:** `feat: dashboard.html live data fetch with skeleton and error handling (#002)`
