import logging
import os
from datetime import datetime, timezone

from src.services.weather import get_weather
from src.services.features import assemble_full_features
from src.model.predict import predict_full
from src.services.cost import wh_to_cost
from src.services.database import insert_prediction, get_last_n_clean_readings, store_drift_event

try:
    from src.services.retrain_trigger import check_drift
except Exception:
    def check_drift(clean_readings: list) -> dict:  # type: ignore[misc]
        return {"drift_detected": False, "drifted_features": [], "deviations": {}}

try:
    from src.services.monitor import check_anomaly as monitor_reading
except Exception:
    def monitor_reading(features: dict) -> dict:  # type: ignore[misc]
        return {"is_anomaly": False, "z_scores": {}, "flagged_features": [], "low_confidence": False}

logger = logging.getLogger(__name__)

_clean_reading_count: int = 0


def _read_sensors() -> tuple[int, dict]:
    lights = int(os.environ.get("SENSOR_LIGHTS", "0"))
    sensors = {}
    for i in range(1, 10):
        sensors[f"T{i}"] = float(os.environ.get(f"SENSOR_T{i}", "20.0"))
        sensors[f"RH_{i}"] = float(os.environ.get(f"SENSOR_RH_{i}", "50.0"))
    return lights, sensors


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

    monitor_result = monitor_reading(features)
    low_confidence = monitor_result.get(
        "low_confidence", monitor_result.get("is_anomaly", False)
    )

    try:
        insert_prediction({
            "tier": "full",
            "predicted_wh": predicted_wh,
            "predicted_kwh": predicted_kwh,
            "estimated_cost_ngn": estimated_cost_ngn,
            "location": location,
            "input_features": features,
            "low_confidence": low_confidence,
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
        except Exception:
            logger.exception("Scheduler: drift check failed")
        finally:
            _clean_reading_count = 0
