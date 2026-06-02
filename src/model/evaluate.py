import json
import pathlib
from typing import Any

import pandas as pd
from sklearn.ensemble import RandomForestRegressor, ExtraTreesRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import r2_score
from xgboost import XGBRegressor
from lightgbm import LGBMRegressor
from catboost import CatBoostRegressor


def select_best_by_r2(candidates: list[tuple[str, Any, float]]) -> tuple[str, Any, float]:
    if not candidates:
        raise ValueError("candidates list is empty")
    return max(candidates, key=lambda t: t[2])


def select_best_by_mape(candidates: list[tuple]) -> tuple:
    return min(candidates, key=lambda c: c[2])


def train_all_models(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_test: pd.DataFrame,
    y_test: pd.Series,
) -> tuple[Any, float]:
    models = [
        ("RandomForest", RandomForestRegressor(n_jobs=-1, random_state=42)),
        ("XGBoost", XGBRegressor(n_jobs=-1, random_state=42, verbosity=0)),
        ("LightGBM", LGBMRegressor(n_jobs=-1, random_state=42, verbose=-1)),
        ("CatBoost", CatBoostRegressor(verbose=0, random_state=42)),
        ("ExtraTrees", ExtraTreesRegressor(n_jobs=-1, random_state=42)),
        ("Ridge", Ridge()),
    ]
    candidates = []
    for name, model in models:
        model.fit(X_train, y_train)
        score = r2_score(y_test, model.predict(X_test))
        candidates.append((name, model, score))
    _, best_model, best_r2 = select_best_by_r2(candidates)
    return best_model, best_r2


def write_leaderboard(section: str, scores: dict, metric: str, path: pathlib.Path) -> None:
    existing = json.loads(path.read_text()) if path.exists() else {}
    best = min(scores, key=scores.get) if metric == "mape" else max(scores, key=scores.get)
    existing[section] = [
        {"model": name, metric: round(score, 6), "winner": name == best}
        for name, score in scores.items()
    ]
    path.write_text(json.dumps(existing, indent=2))
