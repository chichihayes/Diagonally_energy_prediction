import json
import pathlib
from typing import Any


def select_best_by_r2(candidates: list[tuple[str, Any, float]]) -> tuple[str, Any, float]:
    if not candidates:
        raise ValueError("candidates list is empty")
    return max(candidates, key=lambda t: t[2])


def write_leaderboard(section: str, scores: dict, metric: str, path: pathlib.Path) -> None:
    existing = json.loads(path.read_text()) if path.exists() else {}
    best = min(scores, key=scores.get) if metric == "mape" else max(scores, key=scores.get)
    existing[section] = [
        {"model": name, metric: round(score, 6), "winner": name == best}
        for name, score in scores.items()
    ]
    path.write_text(json.dumps(existing, indent=2))
