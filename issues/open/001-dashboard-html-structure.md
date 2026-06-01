---
epic: E2-smart-home-dashboard
feature: F3
issue: 001
slug: dashboard-html-structure
---

# 001 — Build dashboard.html structure

## Goal

A homeowner opens dashboard.html and sees a fully laid-out, responsive page
with a hero card, a 9-room sensor grid, and an outside conditions strip —
all showing placeholder dashes before any data loads.

## User Story

As a Smart Home homeowner, I want to open dashboard.html and immediately see
the correct layout with clearly labelled sections, so that when live data
loads the page feels familiar and nothing jumps around.

## Reference Docs

- `docs/architecture.md` — frontend file layout (frontend/dashboard.html,
  frontend/assets/app.js, frontend/assets/style.css)
- `docs/api-contracts.md` — GET /api/v1/predictions response shape (confirms
  which fields the hero card must display)

## Acceptance Criteria

- [ ] dashboard.html renders a hero card with four labelled slots:
      `id="predicted-wh"`, `id="predicted-kwh"`, `id="estimated-cost"`,
      `id="last-updated"` — each showing "—" as placeholder text on load
- [ ] Sensor grid contains exactly 9 room tiles, each with
      `data-room="N"` (N = 1–9), a room name heading ("Room N"),
      a temperature slot (`class="room-temp"`) and a humidity slot
      (`class="room-humidity"`) — each showing "—" on load
- [ ] Outside conditions strip contains 5 labelled value slots:
      `id="w-t-out"`, `id="w-rh-out"`, `id="w-windspeed"`,
      `id="w-visibility"`, `id="w-tdewpoint"` — each showing "—" on load
- [ ] Page renders without any console errors in Chrome at 375 px width and
      at 1024 px width
- [ ] At ≤ 639 px: hero card is full-width, sensor tiles stack in a
      single column or two-column grid, conditions strip stacks vertically
- [ ] At ≥ 640 px: hero card is centred with max-w-2xl, sensor tiles are
      in a 3-column grid, conditions strip is horizontal
- [ ] Tailwind CSS is loaded via CDN — no build step required

## Files to Modify

- `frontend/dashboard.html` — create (does not exist yet)
- `frontend/assets/style.css` — add any custom rules not covered by Tailwind

## Out of Scope

- Fetching data from the API (Issue 002)
- Auto-refresh timer (Issue 003)
- Prediction history or charts (F4)
- Manual sensor input — dashboard is read-only

## Implementation Plan

### Step 1 — Scaffold dashboard.html with Tailwind CDN and three-section layout

**Test (manual):** Open dashboard.html in a browser with no server running.
Confirm the page renders without console errors. Confirm three visually
distinct sections are present: hero card, sensor grid, weather strip.

**File:** `frontend/dashboard.html`

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Diagonally — Smart Home Dashboard</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <link rel="stylesheet" href="assets/style.css" />
</head>
<body class="bg-gray-50 min-h-screen p-4">
  <!-- hero card, sensor grid, weather strip go here -->
  <script src="assets/app.js"></script>
</body>
</html>
```

### Step 2 — Hero card with four labelled slots

**Test (manual):** Load dashboard.html. Inspect the DOM. Confirm four elements
exist with IDs `predicted-wh`, `predicted-kwh`, `estimated-cost`,
`last-updated`, each containing the text "—".

**File:** `frontend/dashboard.html`

```html
<section class="max-w-2xl mx-auto bg-white rounded-2xl shadow p-6 mb-6">
  <h1 class="text-lg font-semibold text-gray-700 mb-4">Current Prediction</h1>
  <div class="grid grid-cols-2 sm:grid-cols-4 gap-4 text-center">
    <div>
      <p class="text-xs text-gray-500 uppercase tracking-wide">Wh</p>
      <p id="predicted-wh" class="text-2xl font-bold text-indigo-600">—</p>
    </div>
    <div>
      <p class="text-xs text-gray-500 uppercase tracking-wide">kWh</p>
      <p id="predicted-kwh" class="text-2xl font-bold text-indigo-600">—</p>
    </div>
    <div>
      <p class="text-xs text-gray-500 uppercase tracking-wide">Est. Cost</p>
      <p id="estimated-cost" class="text-2xl font-bold text-green-600">—</p>
    </div>
    <div>
      <p class="text-xs text-gray-500 uppercase tracking-wide">Last Updated</p>
      <p id="last-updated" class="text-sm text-gray-400">—</p>
    </div>
  </div>
</section>
```

### Step 3 — 9-room sensor grid

**Test (manual):** Load dashboard.html. Run in console:
`document.querySelectorAll('[data-room]').length` → must return `9`.
Run `document.querySelector('[data-room="5"] .room-temp').textContent` → must
return `"—"`.

**File:** `frontend/dashboard.html`

```html
<section class="max-w-2xl mx-auto mb-6">
  <h2 class="text-base font-semibold text-gray-700 mb-3">Room Conditions</h2>
  <div class="grid grid-cols-1 sm:grid-cols-3 gap-3" id="sensor-grid">
    <!-- rooms 1–9 rendered identically -->
    <div data-room="1" class="bg-white rounded-xl shadow p-4">
      <p class="font-medium text-gray-600 mb-2">Room 1</p>
      <p class="text-sm text-gray-500">Temp: <span class="room-temp font-semibold">—</span> °C</p>
      <p class="text-sm text-gray-500">Humidity: <span class="room-humidity font-semibold">—</span> %</p>
    </div>
    <!-- repeat data-room="2" through data-room="9" with same structure -->
  </div>
</section>
```

### Step 4 — Outside conditions strip

**Test (manual):** Load dashboard.html. Run in console:
`document.getElementById('w-windspeed').textContent` → must return `"—"`.
Confirm all five IDs exist: `w-t-out`, `w-rh-out`, `w-windspeed`,
`w-visibility`, `w-tdewpoint`.

**File:** `frontend/dashboard.html`

```html
<section class="max-w-2xl mx-auto bg-white rounded-2xl shadow p-6">
  <h2 class="text-base font-semibold text-gray-700 mb-3">Outside Conditions</h2>
  <div class="flex flex-wrap gap-4 text-center">
    <div><p class="text-xs text-gray-500">Temp (°C)</p><p id="w-t-out" class="font-semibold">—</p></div>
    <div><p class="text-xs text-gray-500">Humidity (%)</p><p id="w-rh-out" class="font-semibold">—</p></div>
    <div><p class="text-xs text-gray-500">Wind (m/s)</p><p id="w-windspeed" class="font-semibold">—</p></div>
    <div><p class="text-xs text-gray-500">Visibility (km)</p><p id="w-visibility" class="font-semibold">—</p></div>
    <div><p class="text-xs text-gray-500">Dew Point (°C)</p><p id="w-tdewpoint" class="font-semibold">—</p></div>
  </div>
</section>
```

### Step 5 — Responsive layout verification

**Test (manual):** Open Chrome DevTools. Toggle device toolbar to "iPhone SE"
(375 × 667 px). Confirm sensor tiles stack without horizontal overflow.
Toggle to "Desktop" (1280 × 800 px). Confirm 3-column sensor grid and centred
hero card.

**File:** `frontend/dashboard.html` — Tailwind classes already applied in
Steps 2–4. No additional code needed if grid-cols-1 / sm:grid-cols-3 are set.

## Git

- **Branch:** `feat/001-dashboard-html-structure`
- **Commit format:** `feat(frontend): scaffold dashboard.html with hero card, sensor grid, and weather strip`
- **PR title:** `feat: dashboard.html static layout — hero card, 9-room grid, weather strip (#001)`
