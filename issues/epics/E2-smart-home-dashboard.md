# E2 — Smart Home Live Dashboard

## Goal

A homeowner with Zigbee sensors installed in every room can open the dashboard and see their current predicted appliance consumption, estimated NGN cost, all nine room sensor readings, and outside weather conditions — updated automatically every 15 minutes with no manual input required.

---

## User Stories

- As a Smart Home homeowner, I want the app to submit my sensor readings automatically so I never have to enter anything manually.
- As a Smart Home homeowner, I want to see the latest prediction and NGN cost the moment I open the dashboard, without clicking anything.
- As a Smart Home homeowner, I want to see all my room temperatures and humidity readings in one view so I can understand what is driving my consumption.
- As a Smart Home homeowner, I want to see my prediction history as a chart so I can spot trends throughout the day.

---

## Features

1. **APScheduler auto-submission** — Runs inside the FastAPI process. Every 15 minutes, fetches the latest Zigbee sensor values (T1–T9, RH_1–RH_9, lights) and the homeowner's location, then calls `POST /api/v1/predict/full` internally and stores the result in Supabase.

2. **POST /api/v1/predict/full endpoint** — Accepts 19 sensor fields + `location`; fetches 6 outside weather features from OpenWeatherMap (10-min cache); assembles 25-feature dict; runs `model_full.joblib`; converts Wh → kWh → NGN; stores row in Supabase; returns `predicted_wh`, `predicted_kwh`, `estimated_cost_ngn`.

3. **Live dashboard (`dashboard.html`)** — Hero prediction card (Wh + kWh + NGN), 9-room sensor grid (temperature + humidity per room), outside conditions strip (T_out, RH_out, Windspeed, Visibility, Tdewpoint), "last updated" timestamp, and client-side 15-minute auto-refresh.

4. **Prediction history chart + table** — A sparkline chart of the last 24 hours of predicted Wh pulled from Supabase, plus a table of the 10 most recent readings.

---

## Out of Scope

- Manual input of sensor readings — Smart Home tier is fully automated
- Sensor hardware installation or configuration — outside app scope
- Real-time push (WebSocket/SSE) — client-side polling every 15 min is sufficient for demo
- Per-room consumption breakdown — one total appliance figure only
- Alerts or notifications when consumption spikes
