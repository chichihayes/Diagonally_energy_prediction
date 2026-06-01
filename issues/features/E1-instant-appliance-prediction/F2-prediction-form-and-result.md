---
epic: E1-instant-appliance-prediction
feature: F2
slug: prediction-form-and-result
---

# F2 — Prediction form and result card (simple.html)

## Goal

A homeowner opens simple.html, enters lights usage (Wh), one room temperature
(T1 °C), and their city name, clicks submit, and immediately sees their
predicted appliance consumption and estimated electricity cost in NGN — along
with the five outside weather values that were used. The form validates inputs
inline and shows a spinner during the API call.

## User Story

As a homeowner with no sensors, I want to fill in three fields and see my
predicted energy usage and cost in seconds, so I can decide whether to reduce
my appliance use before the bill arrives.

## Issues

1. **Build simple.html form** — Three fields: lights (number, Wh), T1 (number,
   °C), city (text). Inline validation: all fields required, lights ≥ 0,
   T1 between -20 and 60. "Get Prediction" button shows a spinner and disables
   on submit. Tailwind CSS via CDN. Responsive on mobile and desktop.

2. **Implement app.js fetch call and result card** — On valid submit, POST to
   /api/v1/predict/simple with JSON body. On 200: render result card showing
   predicted Wh (hero value), predicted kWh, estimated cost in NGN, and a
   weather factors grid (T_out, RH_out, Windspeed, Visibility, Tdewpoint).
   On error: show inline error message with the HTTP status reason.

3. **Wire up and manually verify** — Open simple.html in a browser with the
   API running locally. Submit valid values, confirm result card renders.
   Submit with a missing field, confirm inline error appears without a page
   reload.

## Out of Scope

- Prediction history table (F3)
- Authentication or saved preferences
- Smart Home tier form (full.html)
- Forecast display
