import logging
import os
from datetime import datetime, timezone

import joblib
import pandas as pd

from src.services.data_loader import MODEL_FEATURES, APPLIANCE_COLS
from src.model.predict import predict_full
from src.services.cost import wh_to_cost
from src.services.database import insert_prediction, get_last_n_clean_readings, store_drift_event
from src.services.retrain_trigger import check_drift, run_retraining_if_ready

try:
    from src.services.monitor import check_anomaly as monitor_reading
except Exception:
    def monitor_reading(features: dict) -> dict:  # type: ignore[misc]
        return {"is_anomaly": False, "z_scores": {}, "flagged_features": [], "low_confidence": False}

logger = logging.getLogger(__name__)

_clean_reading_count: int = 0
_test_df: pd.DataFrame | None = None
_test_row_index: int = 0
_scaler = None

_TEST_CSV = os.environ.get("TEST_SPLIT_PATH", "data/processed/test.csv")
_SCALER_PATH = os.environ.get("SCALER_PATH", "src/model/trained/scaler.joblib")


def _get_test_df() -> pd.DataFrame:
    global _test_df
    if _test_df is None:
        _test_df = pd.read_csv(_TEST_CSV, index_col=0, parse_dates=True)
    return _test_df


def _get_scaler():
    global _scaler
    if _scaler is None:
        try:
            _scaler = joblib.load(_SCALER_PATH)
        except (FileNotFoundError, OSError):
            pass
    return _scaler


def _get_next_test_row() -> pd.Series:
    global _test_row_index
    df = _get_test_df()
    row = df.iloc[_test_row_index % len(df)]
    _test_row_index += 1
    return row


def fetch_row_counts() -> tuple[int, int]:
    from src.services.database import supabase as _db
    clean = _db.table("predictions").select("id", count="exact").eq("low_confidence", False).execute().count or 0
    total = _db.table("predictions").select("id", count="exact").execute().count or 0
    return clean, total


def submit_smart_home_reading() -> None:
    global _clean_reading_count

    try:
        row = _get_next_test_row()
    except Exception:
        logger.exception("Scheduler: failed to read test split row — skipping tick")
        return

    # Raw (unscaled) features for drift detection and storage
    raw_features = {feat: float(row[feat]) for feat in MODEL_FEATURES if feat in row.index}

    # Apply scaler for model inference if available
    scaler = _get_scaler()
    if scaler is not None:
        import numpy as np
        feat_arr = [raw_features[f] for f in MODEL_FEATURES if f in raw_features]
        scaled_arr = scaler.transform([feat_arr])[0]
        model_features = dict(zip(MODEL_FEATURES, scaled_arr))
    else:
        model_features = raw_features

    try:
        predicted_wh = predict_full(model_features)
    except Exception:
        logger.exception("Scheduler: model inference failed — skipping tick")
        return

    predicted_kwh, estimated_cost_gbp = wh_to_cost(predicted_wh)

    monitor_result = monitor_reading(raw_features)
    low_confidence = monitor_result.get(
        "low_confidence", monitor_result.get("is_anomaly", False)
    )

    # Per-appliance actual values from test row
    per_appliance = {}
    col_map = {
        "Fridge": "fridge_wh",
        "ChestFreezer": "chest_freezer_wh",
        "UprightFreezer": "upright_freezer_wh",
        "TumbleDryer": "tumble_dryer_wh",
        "WashingMachine": "washing_machine_wh",
        "Dishwasher": "dishwasher_wh",
        "Computer": "computer_wh",
        "Television": "television_wh",
        "ElectricHeater": "electric_heater_wh",
    }
    for src_col, dest_col in col_map.items():
        per_appliance[dest_col] = float(row[src_col]) if src_col in row.index else 0.0

    try:
        insert_prediction({
            "tier": "full",
            "predicted_wh": predicted_wh,
            "predicted_kwh": predicted_kwh,
            "estimated_cost_gbp": estimated_cost_gbp,
            "input_features": raw_features,
            "low_confidence": low_confidence,
            "aggregate_wh": float(row["aggregate_wh"]) if "aggregate_wh" in row.index else predicted_wh,
            **per_appliance,
        })
    except Exception:
        logger.exception("Scheduler: Supabase insert failed — skipping tick")
        return

    if not low_confidence:
        _clean_reading_count += 1

    if _clean_reading_count >= 100:
        try:
            clean_rows = get_last_n_clean_readings(100)
            drift_result = check_drift(clean_rows)
            store_drift_event({
                **drift_result,
                "clean_row_count": 100,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
            clean_count, total_count = fetch_row_counts()
            run_retraining_if_ready(
                drift_detected=drift_result["drift_detected"],
                clean_row_count=clean_count,
                total_row_count=total_count,
            )
        except Exception:
            logger.exception("Scheduler: drift check/retrain failed")
        finally:
            _clean_reading_count = 0
