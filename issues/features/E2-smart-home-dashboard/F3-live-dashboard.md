---
epic: E2-smart-home-dashboard
feature: F3
slug: live-dashboard
---

# F3 — Live dashboard (dashboard.html)

## Goal

A homeowner with Zigbee sensors opens dashboard.html and immediately sees:
the latest predicted appliance consumption (Wh and kWh) and estimated NGN cost
as a hero card; all nine room temperatures and humidity readings in a sensor
grid; current outside weather conditions; and the timestamp of the last
prediction. The page silently refreshes this data every 15 minutes without
any user action.

## User Story

As a Smart Home homeowner, I want to open my dashboard and see my current
predicted consumption, my room conditions, and my outside weather at a glance —
and have it update every 15 minutes automatically — so I always have an
up-to-date picture of what is driving my energy usage.

## Issues

1. **Build dashboard.html structure** — Hero card (predicted Wh, kWh, NGN cost,
   "last updated" timestamp). 9-room sensor grid: one tile per room showing
   room name, temperature (°C), humidity (%). Outside conditions strip:
   T_out, RH_out, Windspeed, Visibility, Tdewpoint. Tailwind CSS via CDN.
   Responsive on mobile and desktop.

2. **Implement app.js dashboard fetch** — On page load, call
   GET /api/v1/predictions?tier=full&limit=1 to retrieve the latest prediction
   and sensor snapshot. Populate all dashboard sections from the response.
   Show a loading skeleton while the request is in flight. Show an error banner
   if the fetch fails.

3. **Add 15-minute client-side auto-refresh** — Use setInterval in app.js to
   re-fetch and re-render the dashboard every 15 minutes. Update the "last
   updated" timestamp on each refresh. No full page reload — update the DOM
   in place.

## Out of Scope

- Prediction history chart or table (F4)
- Manual sensor input — dashboard is read-only
- WebSocket or SSE push — polling every 15 minutes is sufficient
- Per-room consumption breakdown — one total figure only
