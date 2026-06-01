---
epic: E2-smart-home-dashboard
feature: F4
slug: history-chart-and-table
---

# F4 — Prediction history chart and table

## Goal

Below the live dashboard, the homeowner sees a sparkline chart of their
predicted consumption across the last 24 hours and a table of their 10 most
recent Smart Home predictions. Both are populated from Supabase via the
existing predictions API and refresh alongside the dashboard every 15 minutes.

## User Story

As a Smart Home homeowner, I want to see my consumption trend over the last
24 hours as a chart and my most recent readings in a table, so I can spot
patterns — like a peak in the evening or a drop overnight — without needing
a separate reporting tool.

## Issues

1. **Extend GET /api/v1/predictions for 24-hour range** — Add an optional
   `since` query param (ISO datetime string). When passed, filter predictions
   to `created_at >= since`. Existing `tier` and `limit` params continue to
   work. Write a test for the `since` filter.

2. **Add sparkline chart to dashboard.html** — Load Chart.js via CDN. On page
   load, call GET /api/v1/predictions?tier=full&since=<24h ago> to fetch up to
   96 hourly data points. Render a line chart of predicted_wh over time.
   Label x-axis with hour, y-axis with Wh. Highlight the peak point.

3. **Add history table to dashboard.html** — Below the chart, render a table
   of the 10 most recent full-tier predictions: Time, Wh, kWh, NGN cost.
   Show "No data yet" empty state. Refresh chart and table together with the
   existing 15-minute setInterval.

## Out of Scope

- Aggregation beyond 24-hour window — weekly or monthly trends are E3
- Export or download of history data
- Per-room history — one total figure per prediction only
- Basic tier history on this page — that lives on simple.html (E1/F3)
