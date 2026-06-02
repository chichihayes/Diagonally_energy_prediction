import logging
import os
from datetime import datetime, timezone

from src.services.weather import get_weather
from src.services.features import assemble_full_features
from src.model.predict import predict_full
from src.services.cost import wh_to_cost
from src.services.database import insert_prediction, get_last_n_clean_readings, store_drift_event
from src.services.retrain_trigger import check_drift, run_retraining_if_ready

logger = logging.getLogger(__name__)

_clean_reading_count: int = 0


def _read_sensors() -> tuple[int, dict]:
    lights = int(os.environ.get("SENSOR_LIGHTS", "0"))
    sensors = {}
    for i in range(1, 10):
        sensors[f"T{i}"] = float(os.environ.get(f"SENSOR_T{i}", "20.0"))
        sensors[f"RH_{i}"] = float(os.environ.get(f"SENSOR_RH_{i}", "50.0"))
    return lights, sensors


def fetch_row_counts() -> tuple[int, int]:
    from src.services.database import supabase as _db
    clean = _db.table("predictions").select("id", count="exact").eq("low_confidence", False).execute().count or 0
    total = _db.table("predictions").select("id", count="exact").execute().count or 0
    return clean, total


def submit_smart_home_reading() -> None:
    global _clean_reading_count
    location = os.environ.get("SENSOR_LOCATION", "Lagos")
    lights, sensors = _read_sensors()

    try:
        weather = get_weather(location)
    except Exception:
        logger.exception("Scheduler: weather fetch failed — skipping tick")
        return

    features = assemble_full_features(lights, sensors, weather)

    try:
        predicted_wh = predict_full(features)
    except Exception:
        logger.exception("Scheduler: model inference failed — skipping tick")
        return

    predicted_kwh, estimated_cost_ngn = wh_to_cost(predicted_wh)

    try:
        insert_prediction({
            "tier": "full",
            "predicted_wh": predicted_wh,
            "predicted_kwh": predicted_kwh,
            "estimated_cost_ngn": estimated_cost_ngn,
            "location": location,
            "input_features": features,
        })
    except Exception:
        logger.exception("Scheduler: Supabase insert failed — skipping tick")
        return

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
