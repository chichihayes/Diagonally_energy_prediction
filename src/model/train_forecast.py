import json
import logging

import joblib
import numpy as np
import pandas as pd
from xgboost import XGBRegressor

from src.services.data_loader import load_and_split
from src.services.features import build_lag_matrix

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

_HORIZON = 24  # hours ahead


# ---------------------------------------------------------------------------
# Evaluation helpers
# ---------------------------------------------------------------------------

def _mae(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    return float(np.mean(np.abs(y_true - y_pred)))


def _rmse(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    return float(np.sqrt(np.mean((y_true - y_pred) ** 2)))


def _mape(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    mask = y_true != 0
    if not mask.any():
        return float("inf")
    return float(np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100)


# ---------------------------------------------------------------------------
# Model trainers
# ---------------------------------------------------------------------------

def _train_xgb_lags(train_df: pd.DataFrame, test_df: pd.DataFrame):
    X_train, y_train = build_lag_matrix(train_df)
    X_test, y_test = build_lag_matrix(test_df)
    model = XGBRegressor(n_jobs=-1, random_state=42, verbosity=0)
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    y_true = y_test.values
    return model, _mae(y_true, y_pred), _rmse(y_true, y_pred), _mape(y_true, y_pred)


def _train_mstl(train_df: pd.DataFrame, test_df: pd.DataFrame):
    from statsforecast import StatsForecast
    from statsforecast.models import MSTL, AutoARIMA

    series = train_df["aggregate_wh"].copy()
    # MSTL requires a nixtla-format dataframe
    sf_train = pd.DataFrame({
        "unique_id": "house1",
        "ds": series.index,
        "y": series.values,
    })
    model = StatsForecast(
        models=[MSTL(season_length=[6, 144])],  # 1-hour (6x10min), 24-hour (144x10min)
        freq="10min",
    )
    model.fit(sf_train)
    forecast = model.predict(h=len(test_df))
    y_pred = forecast["MSTL"].values[: len(test_df)]
    y_true = test_df["aggregate_wh"].values[: len(y_pred)]
    return model, _mae(y_true, y_pred), _rmse(y_true, y_pred), _mape(y_true, y_pred)


def _train_chronos(train_df: pd.DataFrame, test_df: pd.DataFrame):
    try:
        from chronos import ChronosPipeline
        import torch
    except ImportError:
        raise ImportError("chronos-forecasting not installed — run: pip install chronos-forecasting")

    pipeline = ChronosPipeline.from_pretrained(
        "amazon/chronos-bolt-small",
        device_map="cpu",
        torch_dtype=torch.float32,
    )
    context = torch.tensor(
        train_df["aggregate_wh"].values, dtype=torch.float32
    ).unsqueeze(0)
    forecast = pipeline.predict(context, prediction_length=len(test_df))
    # forecast shape: (num_samples, batch, horizon)
    median = forecast.median(dim=0).values.squeeze(0).numpy()
    y_pred = median[: len(test_df)]
    y_true = test_df["aggregate_wh"].values[: len(y_pred)]

    # Store context for later inference
    class _ChronosWrapper:
        def __init__(self, pipe, context_arr):
            self.pipe = pipe
            self.context = context_arr

        def predict(self, future: pd.DataFrame) -> pd.DataFrame:
            import torch as _torch
            ctx = _torch.tensor(self.context, dtype=_torch.float32).unsqueeze(0)
            fc = self.pipe.predict(ctx, prediction_length=len(future))
            med = fc.median(dim=0).values.squeeze(0).numpy()
            ds = future["ds"] if "ds" in future.columns else pd.date_range(
                start=pd.Timestamp.now(), periods=len(future), freq="h"
            )
            result = pd.DataFrame({
                "ds": ds.values,
                "yhat": med,
                "yhat_lower": med * 0.85,
                "yhat_upper": med * 1.15,
            })
            return result

    wrapper = _ChronosWrapper(pipeline, train_df["aggregate_wh"].values)
    return wrapper, _mae(y_true, y_pred), _rmse(y_true, y_pred), _mape(y_true, y_pred)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def train_and_save(output_path: str = "src/model/trained/model_forecast.joblib") -> dict:
    train_df, test_df = load_and_split()

    results = {}

    logger.info("Training XGBoost with lag features …")
    xgb_model, xgb_mae, xgb_rmse, xgb_mape = _train_xgb_lags(train_df, test_df)
    results["XGBoost_lags"] = {"model": xgb_model, "mae": xgb_mae, "rmse": xgb_rmse, "mape": xgb_mape}

    logger.info("Training MSTL …")
    try:
        mstl_model, mstl_mae, mstl_rmse, mstl_mape = _train_mstl(train_df, test_df)
        results["MSTL"] = {"model": mstl_model, "mae": mstl_mae, "rmse": mstl_rmse, "mape": mstl_mape}
    except Exception as e:
        logger.warning(f"MSTL training failed: {e}")

    logger.info("Training Chronos-Bolt (Small) …")
    try:
        chronos_model, ch_mae, ch_rmse, ch_mape = _train_chronos(train_df, test_df)
        results["Chronos"] = {"model": chronos_model, "mae": ch_mae, "rmse": ch_rmse, "mape": ch_mape}
    except Exception as e:
        logger.warning(f"Chronos training failed: {e}")

    if not results:
        raise RuntimeError("All forecast models failed to train")

    # Select best by MAPE
    best_name = min(results, key=lambda k: results[k]["mape"])
    best_entry = results[best_name]
    logger.info(f"Best model: {best_name}  MAPE={best_entry['mape']:.2f}%")

    joblib.dump({"model": best_entry["model"], "model_type": best_name}, output_path)

    # Save leaderboard
    leaderboard = [
        {
            "model": name,
            "mae": entry["mae"],
            "rmse": entry["rmse"],
            "mape": entry["mape"],
            "winner": name == best_name,
        }
        for name, entry in results.items()
    ]
    leaderboard_path = output_path.replace("model_forecast.joblib", "forecast_leaderboard.json")
    with open(leaderboard_path, "w") as f:
        json.dump(leaderboard, f, indent=2)

    return {name: entry["mape"] for name, entry in results.items()}
