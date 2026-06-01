# docs/schema.md â€” Diagonally Energy Prediction
<!-- TODO: Fill after running /write-specs -->
## Feature Schema
| Feature | Type | Description |
|---|---|---|
| hour | int | Hour of day (0-23) |
| day_of_week | int | Day of week (0=Mon, 6=Sun) |
| month | int | Month (1-12) |
| is_weekend | int | 1 if Saturday or Sunday |
| lag_1h | float | Consumption 1 hour ago (kWh) |
| lag_24h | float | Consumption 24 hours ago (kWh) |
| lag_168h | float | Consumption 1 week ago (kWh) |
| rolling_mean_3h | float | Rolling mean over last 3 hours |
| rolling_mean_24h | float | Rolling mean over last 24 hours |
| target | float | Actual consumption (kWh) â€” label |
