---
epic: E1-instant-appliance-prediction
feature: F3
slug: prediction-history
---

# F3 — Prediction history table

## Goal

After receiving a prediction, the homeowner sees their last 10 Basic tier
predictions in a table below the result card — ordered most-recent-first —
without navigating away. The table refreshes automatically after each new
prediction so the latest result always appears at the top.

## User Story

As a homeowner, I want to see my past predictions on the same page so I can
compare today's reading against previous ones and spot patterns in my
consumption over time.

## Issues

1. **Implement GET /api/v1/predictions** — Query Supabase predictions table,
   filter by `tier=simple` when query param is passed, order by `created_at`
   descending, return up to `limit` records (default 10, max 50). Response
   fields: id, created_at, predicted_wh, predicted_kwh, estimated_cost_ngn,
   location.

2. **Add history table to simple.html** — On page load, fetch
   GET /api/v1/predictions?tier=simple&limit=10 and render a table with
   columns: Time, Wh, kWh, Cost (NGN). Show "No predictions yet" empty state
   if the response is empty. After each successful prediction POST, re-fetch
   and re-render the table so the new row appears immediately.

3. **Write tests** — test_api.py: GET /api/v1/predictions returns 200 with a
   list; tier filter returns only matching rows; limit param is respected.

## Out of Scope

- Pagination or infinite scroll beyond the 10-row default
- Charts or trend visualisation
- History for the Smart Home (full) tier — separate feature
- Deleting or editing past predictions
