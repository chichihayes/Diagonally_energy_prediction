import pytest


def test_evaluate_returns_highest_r2_model():
    from src.model.evaluate import select_best_by_r2
    dummy = lambda: None
    candidates = [("RF", dummy, 0.80), ("XGB", dummy, 0.91), ("Ridge", dummy, 0.70)]
    name, model, score = select_best_by_r2(candidates)
    assert name == "XGB"
    assert score == 0.91


def test_evaluate_rejects_empty_list():
    from src.model.evaluate import select_best_by_r2
    with pytest.raises(ValueError):
        select_best_by_r2([])
