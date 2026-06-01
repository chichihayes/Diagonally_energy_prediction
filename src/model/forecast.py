import os
from datetime import date, timedelta

import joblib
import pandas as pd

_model = None


def load_forecast_model():
    global _model
    if _model is None:
        path = os.environ.get("MODEL_PATH_FORECAST", "src/model/trained/model_forecast.joblib")
        _model = joblib.load(path)


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
