import json
import pathlib


def write_leaderboard(section: str, scores: dict, metric: str, path: pathlib.Path) -> None:
    existing = json.loads(path.read_text()) if path.exists() else {}
    best = min(scores, key=scores.get) if metric == "mape" else max(scores, key=scores.get)
    existing[section] = [
        {"model": name, metric: round(score, 6), "winner": name == best}
        for name, score in scores.items()
    ]
    path.write_text(json.dumps(existing, indent=2))
