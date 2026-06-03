import json
import os

_STATS_PATH = "src/model/trained/training_stats.json"
_stats = None


def _load_stats() -> dict:
    global _stats
    if _stats is None:
        if not os.path.exists(_STATS_PATH):
            raise FileNotFoundError(
                f"training_stats.json not found at {_STATS_PATH}. "
                f"Run load_and_split() first."
            )
        with open(_STATS_PATH) as f:
            _stats = json.load(f)
    return _stats["appliance_stats"]


def check_anomaly(appliance_values: dict) -> dict:
    stats = _load_stats()
    z_scores = {}
    flagged_appliances = []

    for appliance, value in appliance_values.items():
        if appliance not in stats:
            continue
        mean = stats[appliance]["mean"]
        std = stats[appliance]["std"]
        if std == 0:
            continue
        z = (value - mean) / std
        z_scores[appliance] = round(z, 4)
        if abs(z) > 3:
            direction = "HIGH" if z > 0 else "LOW"
            meaning = (
                "consuming more than normal"
                if direction == "HIGH"
                else "consuming less than normal"
            )
            flagged_appliances.append({
                "appliance": appliance,
                "z_score": round(z, 4),
                "direction": direction,
                "meaning": meaning,
            })

    return {
        "is_anomaly": len(flagged_appliances) > 0,
        "z_scores": z_scores,
        "flagged_appliances": flagged_appliances,
    }
