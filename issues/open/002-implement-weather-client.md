---
id: "002"
slug: implement-weather-client
feature: F1
epic: E1
title: Implement weather.py — OpenWeatherMap client with 10-min cache
status: open
---

# 002 — Implement weather.py — OpenWeatherMap client with 10-min cache

## Goal

A weather service module exists that fetches the five outside features needed by
the Basic tier from OpenWeatherMap by city name, caches results for 10 minutes,
and raises an HTTP 500 if the fetch fails — so the endpoint never blocks on a
repeated network call for the same city within a cache window.

## User Story

As the predict/simple route handler, I want a `get_weather(city: str)` function
so I can retrieve all outside weather features in one call without managing HTTP
requests or caching myself.

## Reference Docs

- `docs/schema.md` — the 5 weather features: T_out, RH_out, Windspeed, Visibility, Tdewpoint
- `docs/architecture.md` — weather.py service boundary: fetch and cache only, no model or DB knowledge
- `CLAUDE.md` — scheduler conventions: cache 10 min; raise HTTPException 500 on failure

## Acceptance Criteria

- [ ] `get_weather("Lagos")` returns a dict with exactly the keys: `T_out`, `RH_out`, `Windspeed`, `Visibility`, `Tdewpoint`
- [ ] All five values are floats
- [ ] A second call to `get_weather("Lagos")` within 10 minutes does not make a second HTTP request (cache hit)
- [ ] A call to `get_weather("Lagos")` after 10 minutes makes a fresh HTTP request (cache miss)
- [ ] If the OpenWeatherMap API returns a non-200 status, `get_weather` raises `HTTPException(status_code=500)`
- [ ] If the network call raises a `requests.RequestException`, `get_weather` raises `HTTPException(status_code=500)`
- [ ] `OPENWEATHERMAP_API_KEY` is read from the environment — never hardcoded
- [ ] Cache is keyed by city name (case-sensitive)

## Files to Modify

- `src/services/weather.py` — create

## Out of Scope

- Fetching `Press_mm_hg` (not used by the simple tier; full tier uses the same module — defer that field to issue 003 if needed)
- Any database reads or writes
- Any model calls
- Frontend display

## Implementation Plan

### Step 1 — write failing tests

**File:** `tests/test_weather.py`

```python
import pytest
from unittest.mock import patch, MagicMock
from fastapi import HTTPException

MOCK_RESPONSE = {
    "main": {"temp": 28.4, "humidity": 82.0, "temp_min": 25.1},
    "wind": {"speed": 3.1},
    "visibility": 10000,
}

def _make_mock(status_code=200, json_data=MOCK_RESPONSE):
    m = MagicMock()
    m.status_code = status_code
    m.json.return_value = json_data
    return m

def test_get_weather_returns_expected_keys():
    from src.services.weather import get_weather
    with patch("src.services.weather._cache", {}):
        with patch("requests.get", return_value=_make_mock()) as mock_get:
            result = get_weather("Lagos")
    assert set(result.keys()) == {"T_out", "RH_out", "Windspeed", "Visibility", "Tdewpoint"}
    assert all(isinstance(v, float) for v in result.values())

def test_get_weather_caches_response():
    from src.services.weather import get_weather
    with patch("src.services.weather._cache", {}):
        with patch("requests.get", return_value=_make_mock()) as mock_get:
            get_weather("Lagos")
            get_weather("Lagos")
    assert mock_get.call_count == 1

def test_get_weather_raises_500_on_bad_status():
    from src.services.weather import get_weather
    with patch("src.services.weather._cache", {}):
        with patch("requests.get", return_value=_make_mock(status_code=401)):
            with pytest.raises(HTTPException) as exc:
                get_weather("Lagos")
    assert exc.value.status_code == 500

def test_get_weather_raises_500_on_network_error():
    import requests
    from src.services.weather import get_weather
    with patch("src.services.weather._cache", {}):
        with patch("requests.get", side_effect=requests.RequestException("timeout")):
            with pytest.raises(HTTPException) as exc:
                get_weather("Lagos")
    assert exc.value.status_code == 500
```

Confirm all four tests fail before implementing.

---

### Step 2 — implement get_weather

**File:** `src/services/weather.py`

```python
import os
import time
import requests
from fastapi import HTTPException

_cache: dict[str, tuple[dict, float]] = {}
_CACHE_TTL = 600  # 10 minutes in seconds

def get_weather(city: str) -> dict:
    now = time.monotonic()
    if city in _cache:
        data, ts = _cache[city]
        if now - ts < _CACHE_TTL:
            return data

    api_key = os.environ["OPENWEATHERMAP_API_KEY"]
    url = "https://api.openweathermap.org/data/2.5/weather"
    try:
        resp = requests.get(url, params={"q": city, "appid": api_key, "units": "metric"}, timeout=5)
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Weather fetch failed: {e}")

    if resp.status_code != 200:
        raise HTTPException(status_code=500, detail=f"Weather API returned {resp.status_code}")

    raw = resp.json()
    data = {
        "T_out": float(raw["main"]["temp"]),
        "RH_out": float(raw["main"]["humidity"]),
        "Windspeed": float(raw["wind"]["speed"]),
        "Visibility": float(raw["visibility"]) / 1000.0,  # API returns metres → km
        "Tdewpoint": float(raw["main"]["temp_min"]),       # approximation; replace with dew point calc if available
    }
    _cache[city] = (data, now)
    return data
```

Confirm all four tests pass.

## Git

- **Branch:** `feat/002-weather-client`
- **Commit format:** `feat(services): implement weather.py with OpenWeatherMap fetch and 10-min TTL cache`
- **PR title:** `feat(services): implement weather.py — OpenWeatherMap client with 10-min cache`
