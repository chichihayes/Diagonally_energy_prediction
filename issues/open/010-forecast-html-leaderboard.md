---
id: "010"
slug: forecast-html-leaderboard
feature: F4
epic: E3
title: Surface leaderboard on forecast.html
status: open
---

# 010 — Surface leaderboard on forecast.html

## Goal

`forecast.html` shows a collapsible "Model performance" section below the
bill projection card. On page load it fetches `GET /api/v1/models/leaderboard`
and renders two tables — regression sorted by R² descending and forecast sorted
by MAPE ascending — with the winner row bold. The section is hidden when the
endpoint returns a non-200 status.

## User Story

As a homeowner viewing the forecast page, I want to see which model is being
used and how accurate each candidate was — so I can trust the predictions
shown above.

## Reference Docs

- `docs/api-contracts.md` — GET /api/v1/models/leaderboard response shape (`regression[].{model,r2,winner}`, `forecast[].{model,mape,winner}`)

## Acceptance Criteria

- [ ] A "Model performance" section exists in `forecast.html` below the bill projection card
- [ ] On `DOMContentLoaded`, the page calls `fetch("/api/v1/models/leaderboard")`
- [ ] The regression table columns are: Model, R², Winner
- [ ] The regression table rows are sorted by R² descending
- [ ] The forecast table columns are: Model, MAPE, Winner
- [ ] The forecast table rows are sorted by MAPE ascending
- [ ] The winner row in each table is rendered with `font-weight: bold`
- [ ] The winner cell displays a "✓" character; non-winner cells are empty
- [ ] If the fetch returns a non-200 status or throws a network error, the entire section remains hidden
- [ ] A toggle button collapses and expands the table body

## Files to Modify

- `frontend/forecast.html` — add collapsible section markup and inline fetch+render script

## Out of Scope

- Extracting the fetch logic into `app.js` — keep it inline in `forecast.html` to minimise scope
- Caching the leaderboard — one fetch per page load is sufficient
- Automated tests — frontend has no automated tests in this project

## Implementation Plan

### Step 1 — forecast.html: add collapsible section markup

**File:** `frontend/forecast.html` — insert directly after the closing `</div>` of the bill
projection card:

```html
<!-- Model performance -->
<div id="model-perf-section" class="mt-6 hidden">
  <button
    id="model-perf-toggle"
    class="flex items-center gap-2 text-sm font-medium text-gray-600 hover:text-gray-900"
    onclick="document.getElementById('model-perf-body').classList.toggle('hidden')"
  >
    <span>Model performance</span>
    <span class="text-xs text-gray-400">(click to expand)</span>
  </button>
  <div id="model-perf-body" class="hidden mt-4 space-y-6">
    <div>
      <h3 class="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">
        Regression models (R²)
      </h3>
      <table class="w-full text-sm border-collapse">
        <thead>
          <tr class="text-left text-gray-500 border-b">
            <th class="pb-1 pr-4">Model</th>
            <th class="pb-1 pr-4">R²</th>
            <th class="pb-1">Winner</th>
          </tr>
        </thead>
        <tbody id="regression-table-body"></tbody>
      </table>
    </div>
    <div>
      <h3 class="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">
        Forecast models (MAPE)
      </h3>
      <table class="w-full text-sm border-collapse">
        <thead>
          <tr class="text-left text-gray-500 border-b">
            <th class="pb-1 pr-4">Model</th>
            <th class="pb-1 pr-4">MAPE</th>
            <th class="pb-1">Winner</th>
          </tr>
        </thead>
        <tbody id="forecast-table-body"></tbody>
      </table>
    </div>
  </div>
</div>
```

---

### Step 2 — forecast.html: add fetch and render script

**File:** `frontend/forecast.html` — add inside the existing `<script>` block, or append
a new `<script>` block before `</body>`:

```javascript
async function loadLeaderboard() {
  try {
    const res = await fetch("/api/v1/models/leaderboard");
    if (!res.ok) return; // section stays hidden on 503 or any error
    const data = await res.json();

    document.getElementById("model-perf-section").classList.remove("hidden");

    // Regression — sort by R² descending
    const regression = [...data.regression].sort((a, b) => b.r2 - a.r2);
    const rBody = document.getElementById("regression-table-body");
    regression.forEach(row => {
      const tr = document.createElement("tr");
      if (row.winner) tr.style.fontWeight = "bold";
      tr.innerHTML =
        `<td class="py-1 pr-4">${row.model}</td>` +
        `<td class="py-1 pr-4">${row.r2.toFixed(4)}</td>` +
        `<td class="py-1">${row.winner ? "✓" : ""}</td>`;
      rBody.appendChild(tr);
    });

    // Forecast — sort by MAPE ascending
    const forecast = [...data.forecast].sort((a, b) => a.mape - b.mape);
    const fBody = document.getElementById("forecast-table-body");
    forecast.forEach(row => {
      const tr = document.createElement("tr");
      if (row.winner) tr.style.fontWeight = "bold";
      tr.innerHTML =
        `<td class="py-1 pr-4">${row.model}</td>` +
        `<td class="py-1 pr-4">${row.mape.toFixed(4)}</td>` +
        `<td class="py-1">${row.winner ? "✓" : ""}</td>`;
      fBody.appendChild(tr);
    });
  } catch (_) {
    // network error — section stays hidden
  }
}

document.addEventListener("DOMContentLoaded", loadLeaderboard);
```

## Git

- **Branch:** `feat/010-forecast-html-leaderboard`
- **Commit format:** `feat(frontend): add collapsible model leaderboard section to forecast.html`
- **PR title:** `feat(frontend): model leaderboard section on forecast.html`
