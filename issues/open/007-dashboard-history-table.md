---
epic: E2-smart-home-dashboard
feature: F4
issue: 007
slug: dashboard-history-table
depends-on: 006-dashboard-sparkline-chart
---

# 007 — Add history table and 15-minute refresh to dashboard.html

## Goal

As a Smart Home homeowner, I can see my 10 most recent predictions in a table below the chart, and both the chart and table refresh automatically every 15 minutes.

## User Story

As a Smart Home homeowner, I want a table showing my latest 10 readings — timestamp, Wh, kWh, and cost — alongside a 15-minute auto-refresh so the dashboard stays current without me reloading the page.

## Reference Docs

- `docs/api-contracts.md` — GET /api/v1/predictions response shape: `id`, `tier`, `predicted_wh`, `predicted_kwh`, `estimated_cost_ngn`, `created_at`
- `docs/architecture.md` — scheduler conventions (15-min interval, setInterval in frontend)

## Acceptance Criteria

- [ ] A `<table id="history-table">` with columns **Time**, **Wh**, **kWh**, **Cost (NGN)** renders below the chart section
- [ ] Table is populated from `GET /api/v1/predictions?tier=full&limit=10`
- [ ] When the response is empty, the table body shows one row: `<td colspan="4">No data yet</td>`
- [ ] `predicted_wh` displayed as integer (rounded); `predicted_kwh` to 4 decimal places; `estimated_cost_ngn` to 2 decimal places with `₦` prefix
- [ ] `created_at` displayed as local time in `DD/MM/YYYY HH:mm` format
- [ ] Chart and table both refresh every 15 minutes via a single `setInterval(…, 900_000)`
- [ ] The refresh re-fetches both chart data and table data (two separate fetch calls is acceptable)

## Files to Modify

- `frontend/dashboard.html`
- `frontend/assets/app.js`

## Out of Scope

- Sorting or filtering the table by column
- Pagination beyond 10 rows (that is E3)
- Basic tier history on this page — that lives on `simple.html` (E1/F3)
- Any backend change — issues 005 and 006 cover the API and chart

## Implementation Plan

### Step 1 — add table markup to `dashboard.html`

**File:** `frontend/dashboard.html`

Add below `#history-chart-section`:

```html
<section id="history-table-section" class="mt-6">
  <h2 class="text-lg font-semibold mb-2">Recent Predictions</h2>
  <table id="history-table" class="w-full text-sm border-collapse">
    <thead>
      <tr class="text-left border-b">
        <th class="py-1 pr-4">Time</th>
        <th class="py-1 pr-4">Wh</th>
        <th class="py-1 pr-4">kWh</th>
        <th class="py-1">Cost (NGN)</th>
      </tr>
    </thead>
    <tbody id="history-table-body">
      <tr><td colspan="4" class="py-2 text-gray-500">Loading…</td></tr>
    </tbody>
  </table>
</section>
```

Manual verification:
- Open `dashboard.html` — table skeleton with headings visible; "Loading…" shown in body

### Step 2 — implement `formatDate(isoString)` in `app.js`

**File:** `frontend/assets/app.js`

```js
function formatDate(isoString) {
    const d   = new Date(isoString);
    const dd  = String(d.getDate()).padStart(2, '0');
    const mm  = String(d.getMonth() + 1).padStart(2, '0');
    const yyyy = d.getFullYear();
    const hh  = String(d.getHours()).padStart(2, '0');
    const min = String(d.getMinutes()).padStart(2, '0');
    return `${dd}/${mm}/${yyyy} ${hh}:${min}`;
}
```

Manual verification:
- Browser console: `formatDate("2026-06-01T14:30:00Z")` returns a string in `DD/MM/YYYY HH:mm` format
- The time portion reflects the local timezone conversion of 14:30 UTC (e.g. `01/06/2026 15:30` in UTC+1)

### Step 3 — implement `fetchHistoryTable()` and `renderHistoryTable(data)` in `app.js`

**File:** `frontend/assets/app.js`

```js
async function fetchHistoryTable() {
    const res  = await fetch('/api/v1/predictions?tier=full&limit=10');
    const data = await res.json();
    renderHistoryTable(data);
}

function renderHistoryTable(predictions) {
    const tbody = document.getElementById('history-table-body');
    if (!predictions.length) {
        tbody.innerHTML = '<tr><td colspan="4" class="py-2 text-gray-500">No data yet</td></tr>';
        return;
    }
    tbody.innerHTML = predictions.map(p => `
        <tr class="border-b last:border-0">
          <td class="py-1 pr-4">${formatDate(p.created_at)}</td>
          <td class="py-1 pr-4">${Math.round(p.predicted_wh)}</td>
          <td class="py-1 pr-4">${p.predicted_kwh.toFixed(4)}</td>
          <td class="py-1">&#8358;${p.estimated_cost_ngn.toFixed(2)}</td>
        </tr>
    `).join('');
}
```

### Step 4 — call `fetchHistoryTable()` on page load

**File:** `frontend/assets/app.js`

Inside the existing `DOMContentLoaded` handler, after the `fetchHistoryChart()` call:

```js
fetchHistoryTable();
```

Manual verification:
- Open `dashboard.html` in browser
- Network tab: `GET /api/v1/predictions?tier=full&limit=10` fires on load
- If predictions exist: table rows render with correct formatting
- If no predictions: "No data yet" row visible

### Step 5 — add 15-minute `setInterval` refresh

**File:** `frontend/assets/app.js`

Add once at the end of the `DOMContentLoaded` handler, after the two `fetch` calls:

```js
setInterval(() => {
    fetchHistoryChart();
    fetchHistoryTable();
}, 15 * 60 * 1000);
```

Manual verification:
- Temporarily set interval to `5_000` in dev
- Network tab shows new requests to both endpoints every 5 seconds
- Chart and table update with latest data after each interval
- Restore to `15 * 60 * 1000` before committing

## Git

- **Branch:** `feat/007-dashboard-history-table`
- **Commit format:** `feat(frontend): add history table and 15-min refresh to dashboard.html`
- **PR title:** `feat: history table and auto-refresh on Smart Home dashboard (F4)`
