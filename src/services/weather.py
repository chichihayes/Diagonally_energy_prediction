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
        "Visibility": float(raw["visibility"]) / 1000.0,  # metres → km
        "Tdewpoint": float(raw["main"]["temp_min"]),       # approximation for dew point
    }
    _cache[city] = (data, now)
    return data
