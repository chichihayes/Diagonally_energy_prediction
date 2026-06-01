# E3 — Energy Forecast & Monthly Bill Projection

## Goal

Any homeowner can enter their city and see a 24-hour hourly forecast and a 7-day daily forecast of their appliance energy consumption — with confidence intervals, peak day and peak hour callouts, and a projected monthly electricity bill in NGN as an optimistic, most likely, and pessimistic range.

---

## User Stories

- As a homeowner, I want to see how my appliance consumption is expected to change over the next 24 hours so I can shift usage to cheaper periods.
- As a homeowner, I want to see a 7-day outlook so I can plan ahead for high-consumption days.
- As a homeowner, I want a projected monthly bill in NGN so I know what to expect before the bill arrives.
- As a homeowner, I want to see the optimistic and pessimistic bill estimates so I understand the range, not just a single number that might mislead me.

---

## Features

1. **GET /api/v1/forecast/24h endpoint** — Accepts `location`; fetches current outside weather from OpenWeatherMap; runs `model_forecast.joblib`; returns hourly forecast array (`ds`, `yhat`, `yhat_lower`, `yhat_upper`, `predicted_kwh`, `estimated_cost_ngn`) plus `peak_hour` and `lowest_hour`.

2. **GET /api/v1/forecast/7d endpoint** — Same inputs; returns daily forecast array plus `peak_day`, `lowest_day`, and `projected_month_bill` (`optimistic_ngn`, `most_likely_ngn`, `pessimistic_ngn`) computed by `cost.py` from the confidence intervals.

3. **Forecast page (`forecast.html`)** — Location input + "Get forecast" button; 24-hour area chart with confidence band (teal line, shaded band), peak hour highlighted amber; 7-day bar chart with peak day highlighted amber; monthly bill projection card showing three NGN values side by side (most likely largest).

4. **GET /api/v1/models/leaderboard endpoint** — Returns R² scores for all 6 regression models and MAPE scores for all 5 time series models, with the winning model marked. Gives homeowners visibility into which model is running and how accurate it is.

---

## Out of Scope

- Forecast horizons beyond 7 days
- Per-appliance or per-room consumption forecasts
- Personalised tariff input — rate is set system-wide via env var
- Alerts when forecast exceeds a threshold
- Historical forecast accuracy tracking
