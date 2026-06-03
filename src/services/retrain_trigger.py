import json
import os
import joblib
from datetime import datetime, timezone
import scripts.run_retraining as _retraining_script
from src.services.database import supabase
from src.services.data_loader import MODEL_FEATURES

_STATS_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "src", "model", "trained", "training_stats.json"
)

with open(_STATS_PATH) as _f:
    _stats = json.load(_f)

_training_means = {feat: _stats[feat]["mean"] for feat in MODEL_FEATURES if feat in _stats}

_CLEAN_ROW_THRESHOLD = 2000
_ANOMALY_RATE_MAX = 0.10

_MODEL_PATH = os.environ.get("MODEL_PATH_FULL", "src/model/trained/model_full.joblib")
_META_PATH = _MODEL_PATH.replace(".joblib", ".meta.json")
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


def _read_meta() -> dict:
    with open(_META_PATH) as f:
        return json.load(f)


def _write_meta(data: dict) -> None:
    with open(_META_PATH, "w") as f:
        json.dump(data, f)


def run_retraining_if_ready(
    drift_detected: bool,
    clean_row_count: int,
    total_row_count: int,
) -> None:
    global _drift_first_detected
    if not should_retrain(drift_detected, clean_row_count, total_row_count):
        return

    old_meta = _read_meta()
    old_r2 = old_meta.get("r2", 0.0)

    result = _retraining_script.run_retraining()
    new_r2 = result["new_r2"]
    model_replaced = new_r2 > old_r2

    if model_replaced:
        joblib.dump(result["best_model"], _MODEL_PATH)
        _write_meta({"r2": new_r2})

    supabase.table("retrain_log").insert({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "trigger_reason": "drift + row_count + anomaly_rate all met",
        "old_model_r2": old_r2,
        "new_model_r2": new_r2,
        "model_replaced": model_replaced,
        "rows_used": result["rows_used"],
    }).execute()

    _drift_first_detected = None
