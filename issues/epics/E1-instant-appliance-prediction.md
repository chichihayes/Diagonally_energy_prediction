# E1 — Instant Appliance Prediction (Basic Tier)

## Goal

A homeowner with no sensors can open the app, enter their lights usage, one room temperature, and their city, and receive a predicted appliance energy consumption in watt-hours with an estimated cost in Nigerian Naira — within seconds, without touching any other settings.

---

## User Stories

- As a homeowner, I want to enter my lights usage and room temperature so I can see how much energy my appliances are likely consuming right now.
- As a homeowner, I want the app to fetch outside weather automatically so I don't have to look it up myself.
- As a homeowner, I want to see which weather conditions are driving my consumption so I know what to act on.
- As a homeowner, I want to see my past predictions so I can track how my usage changes over time.

---

## Features

1. **Prediction form** — Three-field form (`lights` in Wh, `T1` in °C, city name) on `simple.html`. Validates on submit; inline errors per field. "Get prediction" button shows spinner during fetch.

2. **Result card** — Displays predicted Wh (hero), converted kWh, estimated cost in NGN, and a weather factors grid showing the 5 outside values (T_out, RH_out, Windspeed, Visibility, Tdewpoint) auto-fetched from OpenWeatherMap.

3. **Prediction history table** — Shows the homeowner's last 10 Basic tier predictions pulled from Supabase, ordered most-recent-first: timestamp, Wh, kWh, NGN cost.

4. **POST /api/v1/predict/simple endpoint** — Accepts `lights`, `T1`, `location`; fetches weather (10-min cache); assembles 7-feature dict; runs `model_simple.joblib`; converts Wh → kWh → NGN; stores row in Supabase; returns `predicted_wh`, `predicted_kwh`, `estimated_cost_ngn`, `weather_factors`.

---

## Out of Scope

- Sensor readings — this tier requires no hardware
- Appliance-level breakdown — one total figure only
- Per-request weather fetches — responses are cached 10 minutes
- User accounts or saved preferences
- Alerts when consumption is high
