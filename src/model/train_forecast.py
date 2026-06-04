import json
import logging

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor

from src.services.data_loader import MODEL_FEATURES, _UK_MONTHLY_TEMPS, TEST_DATES, DEMO_DATE
from src.services.features import build_lag_matrix

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------

def _mae(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    return float(np.mean(np.abs(y_true - y_pred)))

def _rmse(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    return float(np.sqrt(np.mean((y_true - y_pred) ** 2)))

def _mape(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    mask = y_true != 0
    return float(np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100)


# ---------------------------------------------------------------------------
# Temperature forecast helper
# ---------------------------------------------------------------------------

def _fetch_forecast_temps(dates: list) -> list[tuple[float, float]]:
    """Fetch temperature from Open-Meteo for given dates (forecast or historical)."""
    try:
        import requests
        dates_str = [str(pd.Timestamp(d).date()) for d in dates]
        url = (
            "https://api.open-meteo.com/v1/forecast"
            "?latitude=52.77&longitude=-1.20"
            "&daily=temperature_2m_mean,temperature_2m_min"
            "&timezone=Europe%2FLondon"
            f"&start_date={min(dates_str)}&end_date={max(dates_str)}"
        )
        d = requests.get(url, timeout=10).json()["daily"]
        temp_map = dict(zip(d["time"], zip(d["temperature_2m_mean"], d["temperature_2m_min"])))
        return [temp_map.get(s, _UK_MONTHLY_TEMPS[pd.Timestamp(s).month]) for s in dates_str]
    except Exception:
        return [_UK_MONTHLY_TEMPS[pd.Timestamp(d).month] for d in dates]


# ---------------------------------------------------------------------------
# Recursive multi-step forecast for tree models
# ---------------------------------------------------------------------------

def _recursive_forecast(
    model,
    seed_df: pd.DataFrame,
    n_steps: int,
    future_temps: list[tuple[float, float]] | None = None,
) -> np.ndarray:
    history        = list(seed_df["aggregate_wh"].values)
    heater_history = list(seed_df["ElectricHeater"].values)
    current_time   = seed_df.index[-1] + pd.Timedelta("1D")
    preds = []

    for step in range(n_steps):
        dow = current_time.dayofweek

        if future_temps is not None and step < len(future_temps):
            t_mean, t_min = future_temps[step]
        else:
            t_mean, t_min = _UK_MONTHLY_TEMPS[current_time.month]

        row = {
            "day_of_week":           dow,
            "month":                 current_time.month,
            "is_weekend":            int(dow >= 5),
            "lag_1":                 history[-1],
            "lag_7":                 history[-7]  if len(history) >= 7  else history[0],
            "rolling_mean_7":        float(np.mean(history[-7:]))         if len(history) >= 7        else float(np.mean(history)),
            "heater_lag_1":          heater_history[-1],
            "heater_lag_7":          heater_history[-7]                   if len(heater_history) >= 7 else heater_history[0],
            "heater_rolling_mean_7": float(np.mean(heater_history[-7:]))  if len(heater_history) >= 7 else float(np.mean(heater_history)),
            "temp_mean_c":           t_mean,
            "temp_min_c":            t_min,
        }
        X    = pd.DataFrame([row])[MODEL_FEATURES]
        pred = max(0.0, float(model.predict(X)[0]))
        preds.append(pred)
        history.append(pred)
        heater_history.append(heater_history[-7] if len(heater_history) >= 7 else heater_history[-1])
        current_time += pd.Timedelta("1D")

    return np.array(preds)


# ---------------------------------------------------------------------------
# Production wrapper — implements predict(future_df) -> DataFrame
# ---------------------------------------------------------------------------

class _TreeWrapper:
    def __init__(self, model, seed_df: pd.DataFrame):
        self._model   = model
        self._seed_df = seed_df

    def predict(self, future_df: pd.DataFrame) -> pd.DataFrame:
        future_temps = _fetch_forecast_temps(future_df["ds"].tolist())
        raw = _recursive_forecast(self._model, self._seed_df, len(future_df), future_temps)
        return pd.DataFrame({
            "ds":          future_df["ds"].values,
            "yhat":        raw,
            "yhat_lower":  raw * 0.85,
            "yhat_upper":  raw * 1.15,
        })

    def predict_from_features(self, feature_row: dict) -> float:
        """Single-step prediction from a pre-built 11-feature row."""
        X = pd.DataFrame([feature_row])[MODEL_FEATURES]
        return max(0.0, float(self._model.predict(X)[0]))


# ---------------------------------------------------------------------------
# Entry point — reads from data/processed/ CSVs built by save_processed_splits()
# ---------------------------------------------------------------------------

def train_and_save(output_path: str = "src/model/trained/model_forecast.joblib") -> dict:
    train_df = pd.read_csv("data/processed/train.csv", parse_dates=["datetime"]).set_index("datetime")
    test_df  = pd.read_csv("data/processed/test.csv",  parse_dates=["datetime"]).set_index("datetime")

    logger.info(
        "Training RandomForest on %d days, evaluating on %d strategic test days ...",
        len(train_df), len(test_df),
    )

    X_tr, y_tr = build_lag_matrix(train_df)
    model = RandomForestRegressor(n_estimators=300, max_depth=10, random_state=42, n_jobs=-1)
    model.fit(X_tr, y_tr)

    def _band(wh: float) -> str:
        return "LOW" if wh < 12_000 else ("MID" if wh < 25_000 else "HIGH")

    result_rows = []
    y_true_list: list[float] = []
    y_pred_list: list[float] = []
    for d in TEST_DATES:
        rows = test_df[test_df.index.normalize() == d.normalize()]
        if rows.empty:
            logger.warning("Test date %s not found in test.csv — skipping", d.date())
            continue
        actual_wh = float(rows["aggregate_wh"].iloc[0])
        X_row     = rows[MODEL_FEATURES].iloc[0].to_dict()
        pred_wh   = max(0.0, float(model.predict(pd.DataFrame([X_row]))[0]))
        y_true_list.append(actual_wh)
        y_pred_list.append(pred_wh)
        result_rows.append({
            "Band":         _band(actual_wh),
            "Date":         d.strftime("%Y-%m-%d"),
            "Temp C":       round(float(rows["temp_mean_c"].iloc[0]), 1),
            "Actual Wh":    round(actual_wh),
            "Predicted Wh": round(pred_wh),
            "Error %":      round(abs(pred_wh - actual_wh) / actual_wh * 100, 1),
        })

    y_true = np.array(y_true_list)
    y_pred = np.array(y_pred_list)
    mae    = _mae(y_true, y_pred)
    rmse   = _rmse(y_true, y_pred)
    mape   = _mape(y_true, y_pred)

    results_df = pd.DataFrame(result_rows).sort_values("Band").reset_index(drop=True)
    print(results_df.to_string(index=False))
    print()
    print(f"  MAE  : {mae:,.0f} Wh")
    print(f"  RMSE : {rmse:,.0f} Wh")
    print(f"  MAPE : {mape:.1f}%")

    final_model = _TreeWrapper(model, train_df)
    joblib.dump({"model": final_model, "model_type": "RandomForest"}, output_path)
    logger.info("Model saved -> %s", output_path)

    eval_path = output_path.replace("model_forecast.joblib", "model_evaluation.json")
    with open(eval_path, "w") as f:
        json.dump({
            "model":      "RandomForest",
            "mae":        mae,
            "rmse":       rmse,
            "mape":       mape,
            "evaluation": "9 strategic test days (3 LOW / 3 MID / 3 HIGH)",
            "per_day":    sorted(result_rows, key=lambda r: r["Band"]),
        }, f, indent=2)
    logger.info("Evaluation saved -> %s", eval_path)

    return {"RandomForest": mae}
