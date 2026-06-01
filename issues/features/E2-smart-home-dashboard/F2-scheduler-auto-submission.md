---
epic: E2-smart-home-dashboard
feature: F2
slug: scheduler-auto-submission
---

# F2 — APScheduler auto-submission

## Goal

The FastAPI app starts an APScheduler background job on startup that fires
every 15 minutes. On each tick it reads the latest Zigbee sensor values and
the homeowner's location, calls POST /api/v1/predict/full internally, and
stores the result in Supabase. If the weather fetch or Supabase write fails,
the error is logged and that tick is skipped without crashing the app.

## User Story

As a Smart Home homeowner, I want the app to submit my sensor readings and
store my prediction automatically every 15 minutes so I never have to open
a form or click anything — predictions just appear on my dashboard.

## Issues

1. **Implement scheduler.py** — Define a `submit_smart_home_reading()` function
   that assembles the latest sensor readings and location, makes an internal
   call to the predict/full route (or calls the service layer directly), and
   handles exceptions: log and return on OpenWeatherMap failure; log and return
   on Supabase failure. Never raise — the scheduler must not crash.

2. **Wire APScheduler into FastAPI lifespan (main.py)** — On startup, create
   a BackgroundScheduler, add `submit_smart_home_reading` as an interval job
   with a 15-minute interval, and start the scheduler. On shutdown, shut the
   scheduler down gracefully.

3. **Write tests** — test_api.py: confirm that after app startup the scheduler
   is running; mock the sensor source and assert that `submit_smart_home_reading`
   calls the prediction service; assert that a weather fetch exception is caught
   and does not propagate; assert that a Supabase write exception is caught and
   does not propagate.

## Out of Scope

- Frontend dashboard (F3)
- History chart or table (F4)
- Manual sensor input — Smart Home tier is always automatic
- Real Zigbee hardware integration — sensor values are read from config or
  environment for the demo
