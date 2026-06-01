---
epic: E1-instant-appliance-prediction
feature: F3
issue: 003
slug: prediction-history-table-simple-html
depends-on: 002
---

# 003 — Prediction history table in simple.html

## Goal

As a homeowner, I see my last 10 Basic tier predictions in a table below the result card without navigating away.

## User Story

As a homeowner, I want to see my past Basic tier predictions on the same page so I can compare today's reading against previous ones and spot patterns in my consumption over time.

## Reference Docs

- `docs/api-contracts.md` — GET /api/v1/predictions response shape (columns to display)
- `docs/schema.md` — predicted_wh, predicted_kwh, estimated_cost_ngn field types

## Acceptance Criteria

- [ ] History table section appears below the result card in `simple.html`
- [ ] Table has 4 columns: Time, Wh, kWh, Cost (NGN)
- [ ] On page load, `loadHistory()` is called and the table is populated from `GET /api/v1/predictions?tier=simple&limit=10`
- [ ] If the API returns an empty list, the table shows "No predictions yet" in a full-width cell
- [ ] After a successful prediction POST, `loadHistory()` is called and the new row appears at the top of the table without a page refresh
- [ ] Time column displays `created_at` formatted as `DD MMM YYYY HH:mm` (local time)
- [ ] Wh column shows `predicted_wh` rounded to 1 decimal place
- [ ] kWh column shows `predicted_kwh` rounded to 4 decimal places
- [ ] Cost column shows `estimated_cost_ngn` rounded to 2 decimal places with `₦` prefix
- [ ] Table is responsive — horizontally scrollable on screens narrower than 640px

## Files to Modify

- `frontend/simple.html`
- `frontend/assets/app.js`

## Out of Scope

- Automated JavaScript unit tests (no JS test runner is configured)
- Pagination or load-more beyond the 10-row fetch
- Sorting or filtering the table by column
- Delete or edit actions on rows
- History for any tier other than `simple`

## Implementation Plan

### Step 1 — add history section HTML to simple.html

**File:** `frontend/simple.html`

Add after the result card `<div>` and before `</main>`:

```html
<section id="history-section" class="mt-8">
  <h2 class="text-lg font-semibold mb-3 text-gray-700">Recent Predictions</h2>
  <div class="overflow-x-auto rounded-lg border border-gray-200">
    <table class="min-w-full text-sm text-left text-gray-600">
      <thead class="bg-gray-50 text-xs uppercase text-gray-500">
        <tr>
          <th class="px-4 py-3">Time</th>
          <th class="px-4 py-3">Wh</th>
          <th class="px-4 py-3">kWh</th>
          <th class="px-4 py-3">Cost (NGN)</th>
        </tr>
      </thead>
      <tbody id="history-body">
        <tr id="history-empty">
          <td colspan="4" class="px-4 py-6 text-center text-gray-400">No predictions yet</td>
        </tr>
      </tbody>
    </table>
  </div>
</section>
```

- Verify the section renders correctly in a browser with the result card visible above it

### Step 2 — implement loadHistory() in app.js

**File:** `frontend/assets/app.js`

```javascript
async function loadHistory() {
  const tbody = document.getElementById("history-body");
  const res = await fetch("/api/v1/predictions?tier=simple&limit=10");
  const rows = await res.json();

  if (!rows.length) {
    tbody.innerHTML = `
      <tr id="history-empty">
        <td colspan="4" class="px-4 py-6 text-center text-gray-400">No predictions yet</td>
      </tr>`;
    return;
  }

  tbody.innerHTML = rows.map(row => {
    const time = new Date(row.created_at).toLocaleString("en-GB", {
      day: "2-digit", month: "short", year: "numeric",
      hour: "2-digit", minute: "2-digit"
    });
    return `<tr class="border-t border-gray-100 hover:bg-gray-50">
      <td class="px-4 py-3 whitespace-nowrap">${time}</td>
      <td class="px-4 py-3">${row.predicted_wh.toFixed(1)}</td>
      <td class="px-4 py-3">${row.predicted_kwh.toFixed(4)}</td>
      <td class="px-4 py-3">₦${row.estimated_cost_ngn.toFixed(2)}</td>
    </tr>`;
  }).join("");
}
```

- Manual test: open `simple.html` with the API running — history table populates from stored rows

### Step 3 — call loadHistory() on page load

**File:** `frontend/assets/app.js`

```javascript
document.addEventListener("DOMContentLoaded", () => {
  loadHistory();
});
```

- Manual test: hard-refresh `simple.html` — table is populated before any new prediction is submitted

### Step 4 — call loadHistory() after successful prediction POST

**File:** `frontend/assets/app.js`

Inside the existing prediction form submit handler, after the result card is rendered:

```javascript
// existing code: display result card...
await loadHistory();   // refresh table so new row appears at top
```

- Manual test: submit a prediction — result card appears and the new row is immediately visible at the top of the history table without a page refresh

### Step 5 — verify empty state

- Manual test: point `simple.html` at the API with no rows in Supabase — "No predictions yet" message is visible

### Step 6 — verify responsive behaviour

- Manual test: open Chrome DevTools → toggle device toolbar → set width to 375px — table scrolls horizontally, no layout overflow

## Git

- **Branch:** `feat/003-prediction-history-table-simple-html`
- **Commit format:** `feat(frontend): add prediction history table to simple.html`
- **PR title:** `feat: add prediction history table to simple.html (F3)`
