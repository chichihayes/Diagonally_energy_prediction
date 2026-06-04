import os
from datetime import date, timedelta

import joblib
import numpy as np
import pandas as pd

from src.model.train_forecast import _fetch_forecast_temps

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
    likely_kwh     = sum(r["predicted_wh"] for r in forecast_items) / 1000
    optimistic_kwh = sum(r["lower_wh"]     for r in forecast_items) / 1000
    pessimistic_kwh = sum(r["upper_wh"]    for r in forecast_items) / 1000
    return {
        "optimistic_gbp":  round(optimistic_kwh * tariff, 2),
        "most_likely_gbp": round(likely_kwh * tariff, 2),
        "pessimistic_gbp": round(pessimistic_kwh * tariff, 2),
        "period": "7 days",
    }


def forecast_single_day(
    date_str: str,
    lag_1: float,
    lag_7: float,
    rolling_mean_7: float,
    heater_lag_1: float,
    heater_lag_7: float,
    heater_rolling_mean_7: float,
    temp_mean_c: float | None = None,
    temp_min_c: float | None = None,
) -> dict:
    if _model is None:
        raise RuntimeError("Forecast model not loaded — run scripts/run_training_forecast.py first")

    try:
        dt = pd.Timestamp(date_str)
    except Exception:
        raise ValueError(f"Cannot parse date: {date_str!r}")

    date_str = dt.strftime("%Y-%m-%d")
    dow = dt.dayofweek

    if temp_mean_c is None or temp_min_c is None:
        fetched       = _fetch_forecast_temps([dt])
        t_mean, t_min = fetched[0]
    else:
        t_mean, t_min = temp_mean_c, temp_min_c

    row = {
        "day_of_week":           dow,
        "month":                 dt.month,
        "is_weekend":            int(dow >= 5),
        "lag_1":                 lag_1,
        "lag_7":                 lag_7,
        "rolling_mean_7":        rolling_mean_7,
        "heater_lag_1":          heater_lag_1,
        "heater_lag_7":          heater_lag_7,
        "heater_rolling_mean_7": heater_rolling_mean_7,
        "temp_mean_c":           t_mean,
        "temp_min_c":            t_min,
    }

    pred_wh  = _model.predict_from_features(row)
    pred_kwh = round(pred_wh / 1000, 4)
    tariff   = _get_tariff()
    cost     = round(pred_kwh * tariff, 2)

    return {
        "date":               date_str,
        "predicted_wh":       round(pred_wh, 1),
        "predicted_kwh":      pred_kwh,
        "estimated_cost_gbp": cost,
        "lower_wh":           round(pred_wh * 0.85, 1),
        "upper_wh":           round(pred_wh * 1.15, 1),
        "temp_mean_c":        round(t_mean, 1),
        "temp_min_c":         round(t_min, 1),
    }


def forecast_7d() -> dict:
    tariff = _get_tariff()
    today  = date.today()
    future = pd.DataFrame(
        {"ds": pd.date_range(start=str(today), periods=7, freq="D")}
    )
    raw  = _model.predict(future)
    rows = raw[["ds", "yhat", "yhat_lower", "yhat_upper"]].head(7)

    forecast = []
    for _, r in rows.iterrows():
        wh  = float(r["yhat"])
        kwh = round(wh / 1000, 6)
        ds  = pd.Timestamp(r["ds"])
        forecast.append({
            "date":               ds.strftime("%Y-%m-%d"),
            "predicted_wh":       wh,
            "predicted_kwh":      kwh,
            "lower_wh":           float(r["yhat_lower"]),
            "upper_wh":           float(r["yhat_upper"]),
            "estimated_cost_gbp": round(kwh * tariff, 2),
        })

    peak_idx = max(range(7), key=lambda i: forecast[i]["predicted_wh"])
    low_idx  = min(range(7), key=lambda i: forecast[i]["predicted_wh"])

    return {
        "forecast":           forecast,
        "peak_day":           (today + timedelta(days=peak_idx)).strftime("%A"),
        "lowest_day":         (today + timedelta(days=low_idx)).strftime("%A"),
        "projected_week_bill": _project_weekly_bill(forecast, tariff),
    }


# ---------------------------------------------------------------------------
# Offline evaluation — rf_retest 9 random days (seed=99)
# ---------------------------------------------------------------------------

_RF_RETEST_DATES = pd.to_datetime([
    "2013-12-01", "2014-01-05", "2014-07-07",
    "2014-08-21", "2014-12-05", "2015-01-24",
    "2015-03-26", "2015-05-27", "2015-07-01",
])

_EVAL_FEATURES = [
    "day_of_week", "month", "is_weekend",
    "lag_1", "lag_7", "rolling_mean_7",
    "heater_lag_1", "heater_lag_7", "heater_rolling_mean_7",
    "temp_mean_c", "temp_min_c",
]


def _band(wh: float) -> str:
    return "LOW" if wh < 12_000 else ("MID" if wh < 25_000 else "HIGH")


def evaluate_rf_retest() -> None:
    """Print per-day evaluation table for the 9 rf_retest dates (seed=99)."""
    if _model is None:
        print("No model loaded — run scripts/run_training_forecast.py first")
        return

    try:
        train = pd.read_csv("data/processed/train.csv", parse_dates=["datetime"])
        test  = pd.read_csv("data/processed/test.csv",  parse_dates=["datetime"])
    except FileNotFoundError as exc:
        print(f"Cannot load processed data: {exc}")
        return

    all_data = (
        pd.concat([train, test])
          .sort_values("datetime")
          .reset_index(drop=True)
    )

    test_df = all_data[all_data["datetime"].isin(_RF_RETEST_DATES)].copy()

    rows, y_true, y_pred = [], [], []
    for _, r in test_df.iterrows():
        actual = float(r["aggregate_wh"])
        pred   = _model.predict_from_features(r[_EVAL_FEATURES].to_dict())
        err    = abs(pred - actual) / actual * 100
        rows.append({
            "Band":         _band(actual),
            "Date":         r["datetime"].strftime("%Y-%m-%d"),
            "Temp C":       round(float(r["temp_mean_c"]), 1),
            "Actual Wh":    round(actual),
            "Predicted Wh": round(pred),
            "Error %":      round(err, 1),
        })
        y_true.append(actual)
        y_pred.append(pred)

    df = pd.DataFrame(rows).sort_values("Band").reset_index(drop=True)

    y_true_arr = np.array(y_true)
    y_pred_arr = np.array(y_pred)
    mae  = float(np.mean(np.abs(y_true_arr - y_pred_arr)))
    rmse = float(np.sqrt(np.mean((y_true_arr - y_pred_arr) ** 2)))
    mape = float(np.mean(np.abs((y_true_arr - y_pred_arr) / y_true_arr)) * 100)

    first_run_mape = 21.4  # original 9 strategic test days

    print(df.to_string(index=False))
    print()
    print(f"  MAE  : {mae:,.0f} Wh")
    print(f"  RMSE : {rmse:,.0f} Wh")
    print(f"  MAPE : {mape:.1f}%")
    print()
    print(f"  First run (original 9 days) MAPE : {first_run_mape}%")
    print(f"  This run  (random 9 days)   MAPE : {mape:.1f}%")
    if mape <= 25:
        print("  Verdict: consistent — result holds on unseen data")
    elif mape <= 40:
        print("  Verdict: moderate — model is less reliable on random days")
    else:
        print("  Verdict: inconsistent — first result was optimistic")


if __name__ == "__main__":
    evaluate_rf_retest()
