---
epic: E3-energy-forecast-and-bill-projection
feature: F3
issue: 010
slug: forecast-7d-bar-chart-and-bill-card
---

# 010 — Implement 7-day bar chart and monthly bill projection card

## Goal

A homeowner submits a city name and sees a 7-day bar chart with the peak day
highlighted in amber, plus a three-column monthly bill card showing optimistic,
most likely, and pessimistic NGN estimates — all from the same form submit that
fetches the 24-hour chart.

## User Story

As a homeowner, I want to see a week-ahead energy outlook and a projected
monthly bill range at a glance, so I can plan whether to reduce consumption
before a high-usage period hits.

## Reference Docs

- `docs/api-contracts.md` — GET /api/v1/forecast/7d response shape:
  `forecast[].date`, `forecast[].predicted_wh`, `peak_day`,
  `projected_month_bill.optimistic_ngn`, `.pessimistic_ngn`, `.most_likely_ngn`
- `docs/architecture.md` — frontend file layout (frontend/forecast.html,
  frontend/assets/app.js)

## Acceptance Criteria

- [ ] On valid form submit, `fetchForecast7d(location)` calls
      `GET /api/v1/forecast/7d?location=<city>` and returns parsed JSON
- [ ] `render7dChart(data, 'chart-7d')` draws a Chart.js bar chart with:
      - X-axis labels = day-of-week strings (e.g. "Mon", "Tue", …) derived
        from `forecast[].date`
      - Y-axis label = "Wh"
      - Dataset labelled "Daily Wh" with `predicted_wh` values
      - Bar matching `data.peak_day` rendered in amber (`#f59e0b`);
        all other bars in indigo (`#6366f1`)
- [ ] `renderBillCard(projected_month_bill)` populates `id="bill-card"` with
      three columns: "Optimistic" (green), "Most Likely" (indigo, visually
      largest), "Pessimistic" (red) — each showing the NGN value as
      "₦X,XXX.XX"
- [ ] Section `id="section-7d"` and `id="section-bill"` become visible after
      rendering
- [ ] If the 7d API returns 400 or 500, the error banner `id="forecast-error"`
      shows the message; sections remain hidden
- [ ] Both the 24h and 7d fetches run concurrently on submit (use
      `Promise.all`) — the spinner stays until both resolve or either rejects

## Files to Modify

- `frontend/assets/app.js` — add `fetchForecast7d`, `render7dChart`,
  `renderBillCard`; update forecast-form submit handler to use `Promise.all`
- `frontend/forecast.html` — no structural changes needed (sections already
  exist from Issue 008)

## Out of Scope

- 24-hour area chart (Issue 009)
- Model leaderboard display (F4)
- Saving forecast results to Supabase
- Any backend changes — API already implemented

## Implementation Plan

### Step 1 — Write `fetchForecast7d(location)`

**Test assertions (console-level with dev server running):**

| Call | Expected |
|---|---|
| `fetchForecast7d('Lagos')` | resolves with `{ forecast: [...], peak_day: '<day string>', projected_month_bill: { optimistic_ngn: <number>, pessimistic_ngn: <number>, most_likely_ngn: <number> } }` |
| `fetchForecast7d('')` | rejects (API returns 400) |

**File:** `frontend/assets/app.js`

```js
async function fetchForecast7d(location) {
  const res = await fetch(`/api/v1/forecast/7d?location=${encodeURIComponent(location)}`);
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Server error ${res.status}`);
  }
  return res.json();
}
```

### Step 2 — Write `render7dChart(data, canvasId)`

**Test (manual):** With dev server running, run in console:

```js
fetchForecast7d('Lagos').then(data => render7dChart(data, 'chart-7d'));
```

Confirm:
- Seven bars appear on `canvas#chart-7d`.
- X-axis shows day abbreviations (Mon, Tue, …).
- One bar is amber; the rest are indigo.
- Hovering a bar shows the predicted Wh value in the tooltip.

**File:** `frontend/assets/app.js`

```js
let chart7d = null;

function render7dChart(data, canvasId) {
  const dayNames = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
  const labels = data.forecast.map(p => {
    const d = new Date(p.date);
    return dayNames[d.getUTCDay()];
  });

  const barColors = labels.map(day =>
    day === data.peak_day ? '#f59e0b' : '#6366f1'
  );

  if (chart7d) chart7d.destroy();
  const ctx = document.getElementById(canvasId).getContext('2d');
  chart7d = new Chart(ctx, {
    type: 'bar',
    data: {
      labels,
      datasets: [{
        label: 'Daily Wh',
        data: data.forecast.map(p => p.predicted_wh),
        backgroundColor: barColors,
      }],
    },
    options: {
      responsive: true,
      plugins: { legend: { display: false } },
      scales: {
        x: { title: { display: true, text: 'Day' } },
        y: { title: { display: true, text: 'Wh' } },
      },
    },
  });
}
```

### Step 3 — Write `renderBillCard(projected_month_bill)`

**Test assertions (console-level):**

Paste the following into the browser console and confirm the rendered HTML
matches the expected structure:

```js
renderBillCard({ optimistic_ngn: 3200, most_likely_ngn: 4200, pessimistic_ngn: 5100 });
document.getElementById('bill-card').querySelectorAll('[data-bill]').length
// → 3
document.querySelector('[data-bill="optimistic"]').textContent.trim()
// → "₦3,200.00"
document.querySelector('[data-bill="most-likely"]').textContent.trim()
// → "₦4,200.00"
document.querySelector('[data-bill="pessimistic"]').textContent.trim()
// → "₦5,100.00"
```

**File:** `frontend/assets/app.js`

```js
function formatNGN(amount) {
  return '₦' + amount.toLocaleString('en-NG', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function renderBillCard(bill) {
  const card = document.getElementById('bill-card');
  card.innerHTML = `
    <div class="grid grid-cols-3 gap-4 text-center">
      <div class="bg-green-50 rounded-xl p-4">
        <p class="text-xs text-green-600 font-medium uppercase tracking-wide mb-1">Optimistic</p>
        <p data-bill="optimistic" class="text-xl font-bold text-green-700">${formatNGN(bill.optimistic_ngn)}</p>
      </div>
      <div class="bg-indigo-50 rounded-xl p-5 ring-2 ring-indigo-400">
        <p class="text-xs text-indigo-600 font-medium uppercase tracking-wide mb-1">Most Likely</p>
        <p data-bill="most-likely" class="text-2xl font-extrabold text-indigo-700">${formatNGN(bill.most_likely_ngn)}</p>
      </div>
      <div class="bg-red-50 rounded-xl p-4">
        <p class="text-xs text-red-600 font-medium uppercase tracking-wide mb-1">Pessimistic</p>
        <p data-bill="pessimistic" class="text-xl font-bold text-red-700">${formatNGN(bill.pessimistic_ngn)}</p>
      </div>
    </div>
  `;
}
```

### Step 4 — Update forecast-form submit handler to use `Promise.all`

**Test (manual):** Submit the form with city "Lagos". Open the Network tab in
DevTools. Confirm two requests fire simultaneously:
- `GET /api/v1/forecast/24h?location=Lagos`
- `GET /api/v1/forecast/7d?location=Lagos`

Confirm all three sections (`section-24h`, `section-7d`, `section-bill`)
become visible after both complete. Confirm the spinner disappears and the
button is re-enabled.

**File:** `frontend/assets/app.js` — replace the submit handler from Issue 009:

```js
document.getElementById('forecast-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  const location = document.getElementById('location').value.trim();
  if (!location) return;

  const errorEl = document.getElementById('forecast-error');
  errorEl.classList.add('hidden');
  errorEl.textContent = '';
  ['section-24h', 'section-7d', 'section-bill'].forEach(id =>
    document.getElementById(id).classList.add('hidden')
  );

  setForecastLoading(true);
  try {
    const [data24h, data7d] = await Promise.all([
      fetchForecast24h(location),
      fetchForecast7d(location),
    ]);

    render24hChart(data24h, 'chart-24h');
    document.getElementById('section-24h').classList.remove('hidden');

    render7dChart(data7d, 'chart-7d');
    document.getElementById('section-7d').classList.remove('hidden');

    renderBillCard(data7d.projected_month_bill);
    document.getElementById('section-bill').classList.remove('hidden');
  } catch (err) {
    errorEl.textContent = err.message;
    errorEl.classList.remove('hidden');
  } finally {
    setForecastLoading(false);
  }
});
```

### Step 5 — End-to-end golden path verification

**Test (manual):** Open forecast.html with the dev server running. Enter
"Lagos" and click "Get Forecast". Confirm:

- Spinner appears immediately.
- Both API calls complete (Network tab shows 200 for both).
- 24-hour area chart is visible with shaded band and amber peak point.
- 7-day bar chart is visible with amber peak bar.
- Monthly bill card shows three columns with ₦ values.
- Button is re-enabled and spinner is gone.
- Page looks correct at 375 px width (iPhone SE) and at 1280 px width.

**File:** No code changes — this validates the full integration of Issues
008, 009, and 010.

## Git

- **Branch:** `feat/010-forecast-7d-bar-chart-and-bill-card`
- **Commit format:** `feat(frontend): implement 7d bar chart and monthly bill projection card`
- **PR title:** `feat: 7-day forecast bar chart and bill projection card with Promise.all fetch (#010)`
