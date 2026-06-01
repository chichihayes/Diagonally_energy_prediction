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


def test_select_best_by_mape_returns_lowest_mape():
    from src.model.evaluate import select_best_by_mape
    candidates = [
        ("Prophet", "model_a", 12.5),
        ("LightGBM_lags", "model_b", 8.1),
        ("XGBoost_lags", "model_c", 10.0),
    ]
    name, model, mape = select_best_by_mape(candidates)
    assert name == "LightGBM_lags"
    assert model == "model_b"
    assert mape == 8.1


def test_select_best_by_mape_single_candidate():
    from src.model.evaluate import select_best_by_mape
    candidates = [("Prophet", "only_model", 15.0)]
    name, model, mape = select_best_by_mape(candidates)
    assert name == "Prophet"
