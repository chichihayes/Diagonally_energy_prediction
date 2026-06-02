import json

_STATS_PATH = "src/model/trained/training_stats.json"

with open(_STATS_PATH) as f:
    _training_stats: dict = json.load(f)


def check_anomaly(features: dict) -> dict:
    z_scores = {}
    flagged = []
    for feat, value in features.items():
        if feat not in _training_stats:
            continue
        mean = _training_stats[feat]["mean"]
        std = _training_stats[feat]["std"]
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
