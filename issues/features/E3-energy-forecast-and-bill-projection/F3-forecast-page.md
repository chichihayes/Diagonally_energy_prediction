---
epic: E3-energy-forecast-and-bill-projection
feature: F3
slug: forecast-page
---

# F3 — Forecast page (forecast.html)

## Goal

A homeowner opens forecast.html, enters their city name, clicks "Get forecast",
and sees: a 24-hour area chart with a confidence band and peak hour highlighted;
a 7-day bar chart with peak day highlighted; and a monthly bill projection card
showing optimistic, most likely, and pessimistic NGN estimates side by side.
All from a single location input — no sensor data required.

## User Story

As a homeowner, I want to enter my city and see a visual 24-hour and 7-day
energy outlook alongside a projected monthly bill range, so I can plan ahead
and take action before a high-consumption period arrives.

## Issues

1. **Build forecast.html structure** — Location text input and "Get Forecast"
   button. Loading spinner shown during fetch. Below the form: 24-hour chart
   placeholder, 7-day chart placeholder, monthly bill projection card. Tailwind
   CSS via CDN. Responsive on mobile and desktop.

2. **Implement 24-hour area chart** — Load Chart.js via CDN. On submit, call
   GET /api/v1/forecast/24h?location=<city>. Render a line chart with a shaded
   confidence band (yhat_lower to yhat_upper). X-axis: hour labels. Y-axis: Wh.
   Highlight the peak_hour data point in amber. Show estimated_cost_ngn as a
   tooltip on hover.

3. **Implement 7-day bar chart + bill projection card** — On the same submit,
   call GET /api/v1/forecast/7d?location=<city>. Render a bar chart of daily
   predicted_wh for each of the 7 days. Highlight peak_day bar in amber.
   Below the chart, render the bill projection card: three columns —
   Optimistic, Most Likely (largest, centre), Pessimistic — each showing the
   NGN value in large text.

## Out of Scope

- Model leaderboard display (F4)
- Sensor data input — forecast is location-only
- Forecast horizons beyond 7 days
- Saving forecast results to Supabase
