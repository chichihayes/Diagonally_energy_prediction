---
epic: E3-energy-forecast-and-bill-projection
feature: F3
issue: 008
slug: forecast-html-structure
---

# 008 — Build forecast.html structure

## Goal

A homeowner opens forecast.html and sees a responsive page with a city input,
"Get Forecast" button, loading spinner, and three clearly labelled placeholder
sections (24-hour chart, 7-day chart, monthly bill card) — all before any API
call is made.

## User Story

As a homeowner, I want to open forecast.html and see the correct layout
immediately on load, so the page feels stable and nothing jumps when forecast
data arrives.

## Reference Docs

- `docs/architecture.md` — frontend file layout (frontend/forecast.html,
  frontend/assets/app.js, frontend/assets/style.css)
- `docs/api-contracts.md` — GET /api/v1/forecast/24h and GET /api/v1/forecast/7d
  query params and response shapes (confirms which sections are needed)

## Acceptance Criteria

- [ ] forecast.html renders a text input `id="location"` with placeholder
      "e.g. Lagos" and a button `id="forecast-btn"` labelled "Get Forecast"
- [ ] A spinner element `id="forecast-spinner"` exists and has `class="hidden"`
      on load
- [ ] A `<canvas id="chart-24h">` element exists inside a labelled section
      "24-Hour Outlook" and is hidden (`class="hidden"`) on load
- [ ] A `<canvas id="chart-7d">` element exists inside a labelled section
      "7-Day Outlook" and is hidden (`class="hidden"`) on load
- [ ] A `<div id="bill-card">` exists inside a labelled section "Monthly Bill
      Projection" and is hidden (`class="hidden"`) on load
- [ ] An error banner `id="forecast-error"` exists and has `class="hidden"`
      on load
- [ ] Page renders without console errors at 375 px width and 1024 px width
- [ ] Tailwind CSS loaded via CDN — no build step required
- [ ] At ≤ 639 px: form is full-width, chart sections stack vertically
- [ ] At ≥ 640 px: form card is centred with max-w-lg, sections centred with
      max-w-2xl

## Files to Modify

- `frontend/forecast.html` — create (does not exist yet)
- `frontend/assets/style.css` — add any custom rules not covered by Tailwind

## Out of Scope

- Fetching forecast data or calling the API (Issues 009, 010)
- Rendering Chart.js charts (Issues 009, 010)
- Bill projection card content (Issue 010)

## Implementation Plan

### Step 1 — Scaffold forecast.html with Tailwind CDN and page skeleton

**Test (manual):** Open forecast.html in a browser with no server running.
Confirm the page title is "Diagonally — Energy Forecast", no console errors
appear, and Tailwind classes take effect (background, font, etc.).

**File:** `frontend/forecast.html`

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Diagonally — Energy Forecast</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <link rel="stylesheet" href="assets/style.css" />
</head>
<body class="bg-gray-50 min-h-screen p-4">
  <!-- form, sections, script go here -->
  <script src="assets/app.js"></script>
</body>
</html>
```

### Step 2 — Add location form with spinner and error banner

**Test (manual):** Load forecast.html. Run in console:
`document.getElementById('location').placeholder` → must return `"e.g. Lagos"`.
`document.getElementById('forecast-btn').textContent.trim()` → must return
`"Get Forecast"`.
`document.getElementById('forecast-spinner').classList.contains('hidden')` →
must return `true`.
`document.getElementById('forecast-error').classList.contains('hidden')` →
must return `true`.

**File:** `frontend/forecast.html`

```html
<div class="max-w-lg mx-auto bg-white rounded-2xl shadow p-6 mb-6">
  <h1 class="text-xl font-bold text-gray-800 mb-4">Energy Forecast</h1>
  <form id="forecast-form" class="flex gap-3">
    <input
      id="location"
      type="text"
      placeholder="e.g. Lagos"
      class="flex-1 border border-gray-300 rounded-lg px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
      required
    />
    <button
      id="forecast-btn"
      type="submit"
      class="bg-indigo-600 text-white px-5 py-2 rounded-lg text-sm font-medium hover:bg-indigo-700 disabled:opacity-50"
    >
      Get Forecast
    </button>
  </form>
  <div id="forecast-spinner" class="hidden mt-4 text-center text-sm text-gray-500">
    Loading…
  </div>
  <div id="forecast-error" class="hidden mt-4 text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg px-4 py-2"></div>
</div>
```

### Step 3 — Add three content sections with hidden placeholders

**Test (manual):** Load forecast.html. Run in console:
`document.getElementById('chart-24h') !== null` → `true`.
`document.getElementById('chart-7d') !== null` → `true`.
`document.getElementById('bill-card') !== null` → `true`.
`document.getElementById('chart-24h').closest('section').classList.contains('hidden')` → `true`.
`document.getElementById('chart-7d').closest('section').classList.contains('hidden')` → `true`.
`document.getElementById('bill-card').closest('section').classList.contains('hidden')` → `true`.

**File:** `frontend/forecast.html`

```html
<!-- 24-hour section -->
<section id="section-24h" class="hidden max-w-2xl mx-auto bg-white rounded-2xl shadow p-6 mb-6">
  <h2 class="text-base font-semibold text-gray-700 mb-4">24-Hour Outlook</h2>
  <canvas id="chart-24h" height="160"></canvas>
</section>

<!-- 7-day section -->
<section id="section-7d" class="hidden max-w-2xl mx-auto bg-white rounded-2xl shadow p-6 mb-6">
  <h2 class="text-base font-semibold text-gray-700 mb-4">7-Day Outlook</h2>
  <canvas id="chart-7d" height="160"></canvas>
</section>

<!-- monthly bill section -->
<section id="section-bill" class="hidden max-w-2xl mx-auto bg-white rounded-2xl shadow p-6 mb-6">
  <h2 class="text-base font-semibold text-gray-700 mb-4">Monthly Bill Projection</h2>
  <div id="bill-card"></div>
</section>
```

### Step 4 — Loading state: disable button and show spinner on submit

**Test (manual):** Submit the form with city "Lagos". Confirm:
- `document.getElementById('forecast-btn').disabled` → `true`
- `document.getElementById('forecast-spinner').classList.contains('hidden')` → `false`
(API call will fail at this stage — that is expected until Issue 009 is done.)

**File:** `frontend/assets/app.js`

```js
function setForecastLoading(on) {
  const btn = document.getElementById('forecast-btn');
  const spinner = document.getElementById('forecast-spinner');
  btn.disabled = on;
  spinner.classList.toggle('hidden', !on);
}
```

Wire in forecast-form submit listener:

```js
document.getElementById('forecast-form').addEventListener('submit', (e) => {
  e.preventDefault();
  const location = document.getElementById('location').value.trim();
  if (!location) return;
  setForecastLoading(true);
  // Issues 009 and 010 complete this handler
});
```

### Step 5 — Responsive layout verification

**Test (manual):** Open Chrome DevTools, toggle "iPhone SE" (375 × 667 px).
Confirm form input is full-width and sections stack vertically without
horizontal overflow. At 1280 × 800 px confirm form card is centred and
sections are centred within max-w-2xl bounds.

**File:** `frontend/forecast.html` — Tailwind classes applied in Steps 2–3
already provide `max-w-lg mx-auto` and `max-w-2xl mx-auto`. No extra code
needed if those classes are present.

## Git

- **Branch:** `feat/008-forecast-html-structure`
- **Commit format:** `feat(frontend): scaffold forecast.html with form, spinner, and section placeholders`
- **PR title:** `feat: forecast.html static layout — form, 24h/7d chart placeholders, bill card (#008)`
