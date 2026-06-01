---
epic: E2-smart-home-dashboard
feature: F4
issue: 006
slug: dashboard-sparkline-chart
depends-on: 005-predictions-since-param
---

# 006 — Add sparkline chart to dashboard.html

## Goal

As a Smart Home homeowner, I can see a line chart of my predicted consumption over the last 24 hours on the dashboard so I can spot trends at a glance.

## User Story

As a Smart Home homeowner, I want a line chart below the live reading showing my appliance energy over the last 24 hours with the peak hour highlighted, so I can see patterns without reading a table.

## Reference Docs

- `docs/api-contracts.md` — GET /api/v1/predictions response shape (`predicted_wh`, `created_at`)
- `docs/architecture.md` — frontend conventions: pure HTML + JS, no build step, Tailwind via CDN

## Acceptance Criteria

- [ ] `dashboard.html` loads Chart.js v4 via CDN (no npm, no build step)
- [ ] On page load, `fetchHistoryChart()` in `app.js` calls `GET /api/v1/predictions?tier=full&since=<iso-24h-ago>&limit=96`
- [ ] A line chart renders with x-axis labels in `HH:mm` format and y-axis labelled `Wh`
- [ ] The data point with the highest `predicted_wh` is rendered in red (`#ef4444`); all other points are blue (`#3b82f6`)
- [ ] When the API returns an empty array, `<p id="chart-empty">No data yet</p>` is visible and the canvas is hidden
- [ ] The canvas is hidden until data loads — no empty axes flash on page load

## Files to Modify

- `frontend/dashboard.html`
- `frontend/assets/app.js`

## Out of Scope

- Zoom or pan on the chart
- Exporting the chart as an image
- Confidence interval bands on the chart
- Any backend change — issue 005 covers the API `since` param

## Implementation Plan

### Step 1 — add Chart.js CDN and chart markup to `dashboard.html`

**File:** `frontend/dashboard.html`

Add in `<head>` (after Tailwind CDN line):
```html
<script src="https://cdn.jsdelivr.net/npm/chart.js@4"></script>
```

Add below the live-reading card:
```html
<section id="history-chart-section">
  <h2 class="text-lg font-semibold mb-2">Last 24 Hours</h2>
  <canvas id="history-chart" hidden></canvas>
  <p id="chart-empty" hidden class="text-gray-500 text-sm">No data yet</p>
</section>
```

- Both `canvas` and `<p>` start `hidden` — JS controls visibility

Manual verification:
- Open `dashboard.html` in browser
- No Chart.js error in console
- Section heading visible; canvas and empty-state paragraph hidden

### Step 2 — implement `buildSinceParam()` in `app.js`

**File:** `frontend/assets/app.js`

```js
function buildSinceParam() {
    return new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString();
}
```

Manual verification:
- Browser console: `buildSinceParam()` returns a valid ISO 8601 UTC string
- The returned timestamp is exactly 24 hours behind `new Date().toISOString()`

### Step 3 — implement `fetchHistoryChart()` in `app.js`

**File:** `frontend/assets/app.js`

```js
async function fetchHistoryChart() {
    const since = buildSinceParam();
    const res = await fetch(
        `/api/v1/predictions?tier=full&since=${encodeURIComponent(since)}&limit=96`
    );
    const data = await res.json();
    renderHistoryChart(data);
}
```

### Step 4 — implement `renderHistoryChart(predictions)` in `app.js`

**File:** `frontend/assets/app.js`

```js
function renderHistoryChart(predictions) {
    const canvas = document.getElementById('history-chart');
    const empty  = document.getElementById('chart-empty');

    if (!predictions.length) {
        canvas.hidden = true;
        empty.hidden  = false;
        return;
    }

    const labels      = predictions.map(p =>
        new Date(p.created_at).toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' })
    );
    const values      = predictions.map(p => p.predicted_wh);
    const maxVal      = Math.max(...values);
    const pointColors = values.map(v => v === maxVal ? '#ef4444' : '#3b82f6');

    canvas.hidden = false;
    empty.hidden  = true;

    new Chart(canvas, {
        type: 'line',
        data: {
            labels,
            datasets: [{
                label: 'Predicted Wh',
                data: values,
                borderColor: '#3b82f6',
                pointBackgroundColor: pointColors,
                tension: 0.3,
                fill: false,
            }]
        },
        options: {
            animation: false,
            scales: {
                y: { title: { display: true, text: 'Wh' } }
            }
        }
    });
}
```

### Step 5 — call `fetchHistoryChart()` on page load

**File:** `frontend/assets/app.js`

Inside the existing `DOMContentLoaded` handler:

```js
document.addEventListener('DOMContentLoaded', () => {
    // … existing init calls …
    fetchHistoryChart();
});
```

Manual verification:
- Open `dashboard.html` in browser
- Network tab: request to `GET /api/v1/predictions?tier=full&since=…&limit=96` fires on load
- If predictions exist: line chart renders, peak point is red
- If no predictions: "No data yet" text visible, canvas hidden

## Git

- **Branch:** `feat/006-dashboard-sparkline-chart`
- **Commit format:** `feat(frontend): add 24-hour sparkline chart to dashboard.html`
- **PR title:** `feat: 24-hour consumption chart on Smart Home dashboard (F4)`
