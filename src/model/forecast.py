import os
from datetime import datetime, timedelta, date

import joblib
import numpy as np
import pandas as pd

try:
    _artifact = joblib.load(
        os.environ.get("MODEL_PATH_FORECAST", "src/model/trained/model_forecast.joblib")
    )
    _model = _artifact["model"] if isinstance(_artifact, dict) else _artifact
except (FileNotFoundError, OSError):
    _artifact = None
    _model = None


def _get_tariff() -> float:
    return float(os.environ["ELECTRICITY_TARIFF_GBP_PER_KWH"])


def _project_weekly_bill(forecast_items: list, tariff: float) -> dict:
    likely_kwh = sum(r["predicted_wh"] for r in forecast_items) / 1000
    optimistic_kwh = sum(r["lower_wh"] for r in forecast_items) / 1000
    pessimistic_kwh = sum(r["upper_wh"] for r in forecast_items) / 1000
    return {
        "optimistic_gbp": round(optimistic_kwh * tariff, 2),
        "most_likely_gbp": round(likely_kwh * tariff, 2),
        "pessimistic_gbp": round(pessimistic_kwh * tariff, 2),
        "period": "7 days",
    }


def forecast_7d() -> dict:
    tariff = _get_tariff()
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
            "estimated_cost_gbp": round(kwh * tariff, 2),
        })

    peak_idx = max(range(7), key=lambda i: forecast[i]["predicted_wh"])
    low_idx = min(range(7), key=lambda i: forecast[i]["predicted_wh"])

    return {
        "forecast": forecast,
        "peak_day": (today + timedelta(days=peak_idx)).strftime("%A"),
        "lowest_day": (today + timedelta(days=low_idx)).strftime("%A"),
        "projected_week_bill": _project_weekly_bill(forecast, tariff),
    }


def forecast_24h() -> list[dict]:
    tariff = _get_tariff()
    model_type = _artifact["model_type"] if isinstance(_artifact, dict) else "Prophet"
    model = _artifact["model"] if isinstance(_artifact, dict) else _artifact

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
    elif model_type == "XGBoost_lags":
        lag_cols = ["lag_1", "lag_6", "lag_144", "lag_1008",
                    "rolling_mean_6", "rolling_mean_144", "rolling_std_6"]
        X_future = pd.DataFrame([{c: 0.0 for c in lag_cols}] * 24)
        yhat_arr = model.predict(X_future)
        items = [
            (future_dates[i], float(yhat_arr[i]),
             float(yhat_arr[i]) * 0.85, float(yhat_arr[i]) * 1.15)
            for i in range(24)
        ]
    elif model_type == "MSTL":
        # statsforecast MSTL predict interface
        forecast_df = model.predict(h=24)
        yhat_arr = forecast_df["MSTL"].values if "MSTL" in forecast_df.columns else forecast_df.iloc[:, 0].values
        items = [
            (future_dates[i], float(yhat_arr[i]),
             float(yhat_arr[i]) * 0.85, float(yhat_arr[i]) * 1.15)
            for i in range(min(24, len(yhat_arr)))
        ]
        # Pad if needed
        while len(items) < 24:
            i = len(items)
            items.append((future_dates[i], 0.0, 0.0, 0.0))
    elif model_type == "Chronos":
        # Chronos pipeline: returns quantile predictions
        context = _artifact.get("context", np.zeros(64))
        context_tensor = np.array(context, dtype=np.float32)
        import torch
        low, median, high = model.predict_quantiles(
            context=torch.from_numpy(context_tensor).unsqueeze(0),
            prediction_length=24,
            quantile_levels=[0.1, 0.5, 0.9],
        )
        items = [
            (future_dates[i],
             float(median[0, i]),
             float(low[0, i]),
             float(high[0, i]))
            for i in range(24)
        ]
    else:
        raise ValueError(f"Unknown model_type: {model_type}")

    result = []
    for ds, yhat, lower, upper in items:
        predicted_kwh = round(yhat / 1000, 3)
        result.append({
            "ds": ds.isoformat() if hasattr(ds, "isoformat") else str(ds),
            "yhat": yhat,
            "yhat_lower": lower,
            "yhat_upper": upper,
            "predicted_kwh": predicted_kwh,
            "estimated_cost_gbp": round(predicted_kwh * tariff, 2),
        })

    return result
