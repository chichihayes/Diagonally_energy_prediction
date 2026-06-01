---
epic: E3-energy-forecast-and-bill-projection
feature: F3
issue: 009
slug: forecast-24h-area-chart
---

# 009 — Implement 24-hour area chart

## Goal

A homeowner submits a city name and sees a line chart with a shaded confidence
band showing predicted appliance energy for the next 24 hours, with the peak
hour highlighted in amber and per-hour cost shown on hover.

## User Story

As a homeowner, I want to see a visual 24-hour energy outlook with a confidence
range and the most expensive hour clearly marked, so I know when to shift usage
before that hour arrives.

## Reference Docs

- `docs/api-contracts.md` — GET /api/v1/forecast/24h response shape:
  `forecast[].hour`, `forecast[].predicted_wh`, `forecast[].lower_wh`,
  `forecast[].upper_wh`, `forecast[].estimated_cost_ngn`, `peak_hour`
- `docs/architecture.md` — frontend file layout (frontend/forecast.html,
  frontend/assets/app.js)

## Acceptance Criteria

- [ ] On valid form submit, `fetchForecast24h(location)` calls
      `GET /api/v1/forecast/24h?location=<city>` and returns parsed JSON
- [ ] `render24hChart(data, 'chart-24h')` draws a Chart.js line chart with:
      - X-axis labels = hour strings formatted as `HH:mm`
      - Y-axis label = "Wh"
      - Dataset labelled "Predicted Wh" with `predicted_wh` values
      - Shaded band dataset using `lower_wh` and `upper_wh` as fill boundaries
- [ ] The data point matching `data.peak_hour` is rendered in amber
      (`#f59e0b`) — all other points use indigo (`#6366f1`)
- [ ] Hovering a data point shows a tooltip containing the hour and
      `estimated_cost_ngn` formatted as "₦X.XX"
- [ ] Section `id="section-24h"` becomes visible (removes `hidden` class)
      after chart renders
- [ ] If the API returns 400 or 500, the error banner `id="forecast-error"`
      shows the message and spinner is hidden; section-24h remains hidden
- [ ] Spinner is hidden and button is re-enabled after fetch completes
      (success or error)

## Files to Modify

- `frontend/forecast.html` — add Chart.js CDN `<script>` tag in `<head>`
- `frontend/assets/app.js` — add `fetchForecast24h`, `render24hChart`, wire
  into the forecast-form submit handler

## Out of Scope

- 7-day chart (Issue 010)
- Bill projection card (Issue 010)
- Saving forecast to Supabase
- Any backend changes — API already implemented

## Implementation Plan

### Step 1 — Add Chart.js via CDN

**Test (manual):** Open forecast.html in a browser. Run in console:
`typeof Chart` → must return `"function"`. No console errors about
failed script loads.

**File:** `frontend/forecast.html` — add in `<head>` before `</head>`:

```html
<script src="https://cdn.jsdelivr.net/npm/chart.js@4"></script>
```

### Step 2 — Write `fetchForecast24h(location)`

**Test (automated console check):** With the dev server running, open
forecast.html and run:

```js
fetchForecast24h('Lagos').then(d => console.log(d.forecast.length, d.peak_hour))
```

Expected: logs a number between 1 and 24 for `forecast.length` and an ISO
string for `peak_hour`. Any `location` that the server accepts returns 200;
passing an empty string returns a rejected promise with status 400.

**Test assertions (unit-style, paste into console):**

| Call | Expected |
|---|---|
| `fetchForecast24h('Lagos')` | resolves with `{ forecast: [...], peak_hour: '<ISO string>', lowest_hour: '<ISO string>' }` |
| `fetchForecast24h('')` | rejects (API returns 400) |

**File:** `frontend/assets/app.js`

```js
async function fetchForecast24h(location) {
  const res = await fetch(`/api/v1/forecast/24h?location=${encodeURIComponent(location)}`);
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Server error ${res.status}`);
  }
  return res.json();
}
```

### Step 3 — Write `render24hChart(data, canvasId)`

**Test (manual):** With the dev server running, fetch real data and render:

```js
fetchForecast24h('Lagos').then(data => render24hChart(data, 'chart-24h'));
```

Confirm:
- A line appears on the canvas `id="chart-24h"`.
- X-axis labels show time strings (e.g. "14:00", "15:00", …).
- A shaded band is visible between lower and upper bounds.
- The amber peak-hour point is visually distinct from the indigo points.

**File:** `frontend/assets/app.js`

```js
let chart24h = null;

function render24hChart(data, canvasId) {
  const labels = data.forecast.map(p => {
    const d = new Date(p.hour);
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false });
  });

  const peakIso = data.peak_hour;
  const pointColors = data.forecast.map(p =>
    p.hour === peakIso ? '#f59e0b' : '#6366f1'
  );
  const pointRadii = data.forecast.map(p =>
    p.hour === peakIso ? 6 : 3
  );

  const mainDataset = {
    label: 'Predicted Wh',
    data: data.forecast.map(p => p.predicted_wh),
    borderColor: '#6366f1',
    pointBackgroundColor: pointColors,
    pointRadius: pointRadii,
    tension: 0.3,
    fill: false,
  };

  const upperDataset = {
    label: 'Upper bound',
    data: data.forecast.map(p => p.upper_wh),
    borderColor: 'transparent',
    pointRadius: 0,
    fill: '+1',
    backgroundColor: 'rgba(99,102,241,0.12)',
  };

  const lowerDataset = {
    label: 'Lower bound',
    data: data.forecast.map(p => p.lower_wh),
    borderColor: 'transparent',
    pointRadius: 0,
    fill: false,
  };

  const costs = data.forecast.map(p => p.estimated_cost_ngn);

  if (chart24h) chart24h.destroy();
  const ctx = document.getElementById(canvasId).getContext('2d');
  chart24h = new Chart(ctx, {
    type: 'line',
    data: { labels, datasets: [upperDataset, lowerDataset, mainDataset] },
    options: {
      responsive: true,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            afterLabel: (item) => {
              if (item.datasetIndex === 2) {
                return `Cost: ₦${costs[item.dataIndex].toFixed(2)}`;
              }
              return null;
            },
          },
        },
      },
      scales: {
        x: { title: { display: true, text: 'Hour' } },
        y: { title: { display: true, text: 'Wh' } },
      },
    },
  });
}
```

### Step 4 — Wire into forecast-form submit handler

**Test (manual):** Submit the form with city "Lagos". Confirm:
- Spinner appears while fetch is in flight.
- `section-24h` becomes visible after data loads.
- `forecast-btn` is re-enabled and spinner is hidden after completion.
- Submitting with an invalid city (one the server rejects) shows the error
  banner with a non-empty message.

**File:** `frontend/assets/app.js` — update the submit handler from Issue 008:

```js
document.getElementById('forecast-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  const location = document.getElementById('location').value.trim();
  if (!location) return;

  const errorEl = document.getElementById('forecast-error');
  errorEl.classList.add('hidden');
  errorEl.textContent = '';

  setForecastLoading(true);
  try {
    const data24h = await fetchForecast24h(location);
    render24hChart(data24h, 'chart-24h');
    document.getElementById('section-24h').classList.remove('hidden');
    // Issue 010 appends 7d fetch here
  } catch (err) {
    errorEl.textContent = err.message;
    errorEl.classList.remove('hidden');
  } finally {
    setForecastLoading(false);
  }
});
```

### Step 5 — Error path verification

**Test (manual):** Temporarily change the fetch URL to a non-existent endpoint
(`/api/v1/forecast/NOTREAL`) and submit. Confirm:
- `forecast-error` becomes visible with a non-empty message.
- `section-24h` remains hidden.
- Button is re-enabled and spinner is hidden.

Restore the correct URL after verifying.

**File:** `frontend/assets/app.js` — no change needed; this validates the
error branch of the handler already written in Step 4.

## Git

- **Branch:** `feat/009-forecast-24h-area-chart`
- **Commit format:** `feat(frontend): implement 24h area chart with confidence band and peak hour highlight`
- **PR title:** `feat: 24-hour forecast area chart with amber peak and cost tooltip (#009)`
