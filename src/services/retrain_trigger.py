import json
import os
import pandas as pd
import joblib
from datetime import datetime, timezone
import scripts.run_retraining as _retraining_script
from src.services.database import supabase, fetch_clean_rows
from src.services.data_loader import MODEL_FEATURES

_STATS_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "src", "model", "trained", "training_stats.json"
)

with open(_STATS_PATH) as _f:
    _stats = json.load(_f)

_training_means = {feat: _stats[feat]["mean"] for feat in MODEL_FEATURES if feat in _stats}

_CLEAN_ROW_THRESHOLD = 2000
_ANOMALY_RATE_MAX = 0.10

_FORECAST_MODEL_PATH = os.environ.get("MODEL_PATH_FORECAST", "src/model/trained/model_forecast.joblib")
_LEADERBOARD_PATH = "src/model/trained/forecast_leaderboard.json"
_drift_first_detected: str | None = None


def check_drift(clean_readings: list[dict]) -> dict:
    if len(clean_readings) < 100:
        raise ValueError(
            f"check_drift requires 100 readings, got {len(clean_readings)}"
        )
    deviations = {}
    drifted = []
    for feature in MODEL_FEATURES:
        if feature not in _training_means:
            continue
        values = [r[feature] for r in clean_readings if feature in r]
        if not values:
            continue
        rolling_mean = sum(values) / len(values)
        training_mean = _training_means[feature]
        if training_mean == 0:
            deviation = 0.0
        else:
            deviation = abs(rolling_mean - training_mean) / abs(training_mean) * 100
        deviations[feature] = round(deviation, 4)
        if deviation > 15:
            drifted.append(feature)
    return {
        "drift_detected": bool(drifted),
        "drifted_features": drifted,
        "deviations": deviations,
    }


def should_retrain(
    drift_detected: bool,
    clean_row_count: int,
    total_row_count: int,
) -> bool:
    if not drift_detected:
        return False
    if clean_row_count < _CLEAN_ROW_THRESHOLD:
        return False
    if total_row_count == 0:
        return False
    anomaly_rate = 1.0 - (clean_row_count / total_row_count)
    return anomaly_rate < _ANOMALY_RATE_MAX


def _read_current_mape() -> float:
    try:
        with open(_LEADERBOARD_PATH) as f:
            data = json.load(f)
        winner = next((e for e in data if e.get("winner")), None)
        return float(winner["mape"]) if winner else float("inf")
    except (FileNotFoundError, KeyError, TypeError):
        return float("inf")


def run_retraining_if_ready(
    drift_detected: bool,
    clean_row_count: int,
    total_row_count: int,
) -> None:
    global _drift_first_detected
    if not should_retrain(drift_detected, clean_row_count, total_row_count):
        return

    old_mape = _read_current_mape()

    raw_rows = fetch_clean_rows()
    clean_rows = [r for r in raw_rows if not r.get("low_confidence", True)]
    if clean_rows:
        df = pd.DataFrame([r["input_features"] for r in clean_rows])
        df["aggregate_wh"] = [r.get("aggregate_wh", r.get("predicted_wh", 0)) for r in clean_rows]
    else:
        df = pd.DataFrame()

    result = _retraining_script.run_retraining(df)
    new_mape = result["new_mape"]
    model_replaced = new_mape < old_mape

    if model_replaced:
        joblib.dump(result["best_model"], _FORECAST_MODEL_PATH)

    supabase.table("retrain_log").insert({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "trigger_reason": "drift + row_count + anomaly_rate all met",
        "old_mape": old_mape,
        "new_mape": new_mape,
        "model_replaced": model_replaced,
        "rows_used": result["rows_used"],
    }).execute()

    _drift_first_detected = None
