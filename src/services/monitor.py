import json
import os

_STATS_PATH = "src/model/trained/training_stats.json"
_training_stats = None


def _load_stats() -> dict:
    global _training_stats
    if _training_stats is None:
        if not os.path.exists(_STATS_PATH):
            raise FileNotFoundError(
                f"training_stats.json not found at {_STATS_PATH}. "
                f"Run load_and_split() to generate it."
            )
        with open(_STATS_PATH) as f:
            _training_stats = json.load(f)
    return _training_stats


def check_anomaly(features: dict) -> dict:
    stats = _load_stats()
    z_scores = {}
    flagged = []
    for feat, value in features.items():
        if feat not in stats:
            continue
        mean = stats[feat]["mean"]
        std = stats[feat]["std"]
        if std == 0:
            continue
        z = (value - mean) / std
        z_scores[feat] = round(z, 4)
        if abs(z) > 3:
            flagged.append(feat)
    return {
        "is_anomaly": len(flagged) > 0,
        "z_scores": z_scores,
        "flagged_features": flagged,
    }
