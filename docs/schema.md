# docs/schema.md â€” Diagonally Energy Prediction
<!-- TODO: Fill after running /write-specs -->
## Feature Schema
| Feature | Type | Unit | Description |
|---|---|---|---|
| Appliances | int | Wh | TARGET — appliance energy use |
| lights | int | Wh | Light energy use |
| T1 | float | °C | Temperature, kitchen |
| RH_1 | float | % | Humidity, kitchen |
| T2 | float | °C | Temperature, living room |
| RH_2 | float | % | Humidity, living room |
| T3 | float | °C | Temperature, laundry room |
| RH_3 | float | % | Humidity, laundry room |
| T4 | float | °C | Temperature, office room |
| RH_4 | float | % | Humidity, office room |
| T5 | float | °C | Temperature, bathroom |
| RH_5 | float | % | Humidity, bathroom |
| T6 | float | °C | Temperature, outside building (north) |
| RH_6 | float | % | Humidity, outside building (north) |
| T7 | float | °C | Temperature, ironing room |
| RH_7 | float | % | Humidity, ironing room |
| T8 | float | °C | Temperature, teenager room 2 |
| RH_8 | float | % | Humidity, teenager room 2 |
| T9 | float | °C | Temperature, parents room |
| RH_9 | float | % | Humidity, parents room |
| T_out | float | °C | Outside temperature (weather station) |
| Press_mm_hg | float | mm Hg | Air pressure |
| RH_out | float | % | Outside humidity |
| Windspeed | float | m/s | Wind speed |
| Visibility | float | km | Visibility |
| Tdewpoint | float | °C | Dew point temperature |
| rv1 | float | — | Random noise variable (dropped at preprocessing) |
| rv2 | float | — | Random noise variable (dropped at preprocessing) |
