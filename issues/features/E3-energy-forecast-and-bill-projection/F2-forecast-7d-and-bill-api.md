---
epic: E3-energy-forecast-and-bill-projection
feature: F2
slug: forecast-7d-and-bill-api
---

# F2 — GET /api/v1/forecast/7d API + bill projection

## Goal

The 7-day forecast endpoint exists and is tested. Given a city name, the API
aggregates daily consumption from model_forecast.joblib, identifies peak and
lowest days, and returns a projected monthly bill as three NGN values —
optimistic, most likely, and pessimistic — derived from the confidence
intervals. The endpoint returns all this in a single JSON response.

## User Story

As a homeowner planning ahead, I want a 7-day consumption outlook and a
projected monthly bill in NGN with an optimistic and pessimistic range so I
can decide now whether to reduce my appliance usage before the bill arrives.

## Issues

1. **Implement forecast.py `forecast_7d` function** — Generate 7 days of daily
   predictions using model_forecast.joblib (freq=D). Return a list of 7 dicts
   with fields: date, predicted_wh, predicted_kwh, lower_wh, upper_wh,
   estimated_cost_ngn. Identify peak_day (highest yhat) and lowest_day (lowest
   yhat) by day name.

2. **Implement bill projection in cost.py** — Add a `project_monthly_bill`
   function. Accept the 7-day forecast array. Scale the 7-day sum to 30 days.
   Compute three NGN values: optimistic (sum of yhat_lower / 1000 × tariff),
   most_likely (sum of yhat / 1000 × tariff), pessimistic (sum of yhat_upper /
   1000 × tariff). Read tariff from ELECTRICITY_TARIFF_NGN_PER_KWH env var.
   Round all values to 2 decimal places.

3. **Implement GET /api/v1/forecast/7d route** — Accept `location` as a query
   param. Call forecast.py for the 7-day array. Call cost.py for the bill
   projection. Return forecast array, peak_day, lowest_day, and
   projected_month_bill (optimistic_ngn, most_likely_ngn, pessimistic_ngn).

4. **Write tests** — test_api.py: valid location returns 200 with a 7-element
   array and a projected_month_bill object; all three bill fields are present
   and optimistic_ngn ≤ most_likely_ngn ≤ pessimistic_ngn. test_cost.py:
   project_monthly_bill returns correct rounded NGN values.

## Out of Scope

- forecast.html frontend (F3)
- Model leaderboard endpoint (F4)
- Forecast horizons beyond 7 days
- Per-homeowner tariff input — rate is read from env var only
