import os
from datetime import datetime, timedelta, date

import joblib
import numpy as np
import pandas as pd

import src.services.weather as _weather_svc

try:
    _artifact = joblib.load(
        os.environ.get("MODEL_PATH_FORECAST", "src/model/trained/model_forecast.joblib")
    )
    _model = _artifact["model"] if isinstance(_artifact, dict) else _artifact
except (FileNotFoundError, OSError):
    _artifact = None
    _model = None


def forecast_7d() -> dict:
    tariff = float(os.environ["ELECTRICITY_TARIFF_NGN_PER_KWH"])
    today = date.today()
    future = pd.DataFrame(
        {"ds": pd.date_range(start=str(today), periods=7, freq="D")}
    )
    raw = _model.predict(future)
    rows = raw[["ds", "yhat", "yhat_lower", "yhat_upper"]].head(7)

    forecast = []
    for _, r in rows.iterrows():
        wh = float(r["yhat"])
        kwh = round(wh / 1000, 6)
        forecast.append({
            "date": r["ds"].strftime("%Y-%m-%d"),
            "predicted_wh": wh,
            "predicted_kwh": kwh,
            "lower_wh": float(r["yhat_lower"]),
            "upper_wh": float(r["yhat_upper"]),
            "estimated_cost_ngn": round(kwh * tariff, 2),
        })

    peak_idx = max(range(7), key=lambda i: forecast[i]["predicted_wh"])
    low_idx = min(range(7), key=lambda i: forecast[i]["predicted_wh"])

    return {
        "forecast": forecast,
        "peak_day": (today + timedelta(days=peak_idx)).strftime("%A"),
        "lowest_day": (today + timedelta(days=low_idx)).strftime("%A"),
    }


def forecast_24h(location: str) -> list[dict]:
    _weather_svc.get_weather(location)

    tariff = float(os.environ["ELECTRICITY_TARIFF_NGN_PER_KWH"])
    model = _artifact["model"]
    model_type = _artifact["model_type"]

    now = datetime.now()
    start = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
    future_dates = pd.date_range(start=start, periods=24, freq="h")

    if model_type == "Prophet":
        future_df = pd.DataFrame({"ds": future_dates})
        raw = model.predict(future_df)
        rows = raw[["ds", "yhat", "yhat_lower", "yhat_upper"]].head(24)
        items = [
            (r["ds"], float(r["yhat"]), float(r["yhat_lower"]), float(r["yhat_upper"]))
            for _, r in rows.iterrows()
        ]
    elif model_type in ("XGBoost_lags", "LightGBM_lags"):
        lag_cols = ["lag_1h", "lag_24h", "lag_168h", "rolling_mean_3h", "rolling_mean_24h"]
        X_future = pd.DataFrame([{c: 0.0 for c in lag_cols}] * 24)
        yhat_arr = model.predict(X_future)
        items = [
            (future_dates[i], float(yhat_arr[i]), float(yhat_arr[i]) * 0.85, float(yhat_arr[i]) * 1.15)
            for i in range(24)
        ]
    else:  # LSTM, TFT
        series = np.zeros(model.input_size)
        yhat, lower, upper = model.predict_from_series(series)
        items = [
            (future_dates[i], float(yhat[i]), float(lower[i]), float(upper[i]))
            for i in range(24)
        ]

    result = []
    for ds, yhat, lower, upper in items:
        predicted_kwh = round(yhat / 1000, 3)
        result.append({
            "ds": ds.isoformat(),
            "yhat": yhat,
            "yhat_lower": lower,
            "yhat_upper": upper,
            "predicted_kwh": predicted_kwh,
            "estimated_cost_ngn": round(predicted_kwh * tariff, 2),
        })

    return result
