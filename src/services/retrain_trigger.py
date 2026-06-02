import json
import os

_STATS_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "src", "model", "trained", "training_stats.json"
)

with open(_STATS_PATH) as _f:
    _stats = json.load(_f)

FULL_FEATURES = [
    "lights", "T1", "RH_1", "T2", "RH_2", "T3", "RH_3",
    "T4", "RH_4", "T5", "RH_5", "T6", "RH_6", "T7", "RH_7",
    "T8", "RH_8", "T9", "RH_9", "T_out", "Press_mm_hg",
    "RH_out", "Windspeed", "Visibility", "Tdewpoint",
]

_training_means = {feat: _stats[feat]["mean"] for feat in FULL_FEATURES}


def check_drift(clean_readings: list[dict]) -> dict:
    if len(clean_readings) < 100:
        raise ValueError(
            f"check_drift requires 100 readings, got {len(clean_readings)}"
        )
    deviations = {}
    drifted = []
    for feature in FULL_FEATURES:
        rolling_mean = sum(r[feature] for r in clean_readings) / len(clean_readings)
        training_mean = _training_means[feature]
        deviation = abs(rolling_mean - training_mean) / training_mean * 100
        deviations[feature] = round(deviation, 4)
        if deviation > 15:
            drifted.append(feature)
    return {
        "drift_detected": bool(drifted),
        "drifted_features": drifted,
        "deviations": deviations,
    }
