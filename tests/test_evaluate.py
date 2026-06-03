import json
import pathlib

import pytest


def test_write_leaderboard_regression_sets_winner_on_highest_r2(tmp_path):
    from src.model.evaluate import write_leaderboard
    scores = {"RandomForest": 0.91, "XGBoost": 0.94, "Ridge": 0.87}
    leaderboard_path = tmp_path / "leaderboard.json"
    write_leaderboard("regression", scores, "r2", leaderboard_path)
    data = json.loads(leaderboard_path.read_text())
    winners = [e for e in data["regression"] if e["winner"]]
    assert len(winners) == 1
    assert winners[0]["model"] == "XGBoost"


def test_write_leaderboard_forecast_sets_winner_on_lowest_mape(tmp_path):
    from src.model.evaluate import write_leaderboard
    scores = {"Prophet": 0.12, "XGBoost": 0.08, "LightGBM": 0.10}
    leaderboard_path = tmp_path / "leaderboard.json"
    write_leaderboard("forecast", scores, "mape", leaderboard_path)
    data = json.loads(leaderboard_path.read_text())
    winners = [e for e in data["forecast"] if e["winner"]]
    assert len(winners) == 1
    assert winners[0]["model"] == "XGBoost"


def test_write_leaderboard_preserves_other_sections(tmp_path):
    from src.model.evaluate import write_leaderboard
    leaderboard_path = tmp_path / "leaderboard.json"
    write_leaderboard("regression", {"RF": 0.91}, "r2", leaderboard_path)
    write_leaderboard("forecast", {"Prophet": 0.15}, "mape", leaderboard_path)
    data = json.loads(leaderboard_path.read_text())
    assert "regression" in data
    assert "forecast" in data


def test_write_leaderboard_each_entry_has_model_metric_and_winner_keys(tmp_path):
    from src.model.evaluate import write_leaderboard
    scores = {"RF": 0.91, "XGB": 0.94}
    leaderboard_path = tmp_path / "leaderboard.json"
    write_leaderboard("regression", scores, "r2", leaderboard_path)
    data = json.loads(leaderboard_path.read_text())
    for entry in data["regression"]:
        assert set(entry.keys()) == {"model", "r2", "winner"}
