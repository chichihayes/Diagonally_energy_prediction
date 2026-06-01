from typing import Any


def select_best_by_r2(candidates: list[tuple[str, Any, float]]) -> tuple[str, Any, float]:
    if not candidates:
        raise ValueError("candidates list is empty")
    return max(candidates, key=lambda t: t[2])
