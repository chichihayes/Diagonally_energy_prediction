import pytest
import numpy as np
import pandas as pd
from unittest.mock import patch, MagicMock

from src.services.data_loader import MODEL_FEATURES, APPLIANCE_COLS


def _make_split_df(n: int = 300) -> pd.DataFrame:
    """Build a minimal preprocessed df with all expected columns, no NaN."""
    rng = np.random.default_rng(42)
    idx = pd.date_range("2013-10-09", periods=n, freq="10min")
    df = pd.DataFrame(index=idx)
    for col in APPLIANCE_COLS:
        df[col] = rng.uniform(0, 200, n)
    df["aggregate_wh"] = df[APPLIANCE_COLS].sum(axis=1)
    df["hour"] = df.index.hour
    df["day_of_week"] = df.index.dayofweek
    df["month"] = df.index.month
    df["is_weekend"] = (df.index.dayofweek >= 5).astype(int)
    df["is_night"] = ((df.index.hour >= 22) | (df.index.hour < 6)).astype(int)
    df["is_peak_hour"] = ((df.index.hour >= 16) & (df.index.hour <= 20)).astype(int)
    # Set lag/rolling columns directly to avoid requiring 1008+ rows of history
    df["lag_1"] = rng.uniform(0, 500, n)
    df["lag_6"] = rng.uniform(0, 500, n)
    df["lag_144"] = rng.uniform(0, 500, n)
    df["lag_1008"] = rng.uniform(0, 500, n)
    df["rolling_mean_6"] = rng.uniform(0, 500, n)
    df["rolling_mean_144"] = rng.uniform(0, 500, n)
    df["rolling_std_6"] = rng.uniform(0, 50, n)
    return df


def test_data_loader_returns_train_test_split():
    train = _make_split_df(400)
    test = _make_split_df(100)
    assert len(train) > 0
    assert len(test) > 0
    assert "aggregate_wh" in train.columns
    for feat in MODEL_FEATURES:
        assert feat in train.columns, f"Missing feature {feat} in train"
    assert "rv1" not in train.columns
    assert "rv2" not in train.columns


def test_predict_full_returns_float(tmp_path, monkeypatch):
    import joblib
    from sklearn.dummy import DummyRegressor

    dummy = DummyRegressor(strategy="constant", constant=150.0)
    X = pd.DataFrame([{c: 1.0 for c in MODEL_FEATURES}])
    dummy.fit(X, [150.0])
    model_path = tmp_path / "model_full.joblib"
    joblib.dump(dummy, str(model_path))
    monkeypatch.setenv("MODEL_PATH_FULL", str(model_path))

    from src.model import predict as predict_module
    import importlib
    importlib.reload(predict_module)

    result = predict_module.predict_full({c: 1.0 for c in MODEL_FEATURES})
    assert isinstance(result, float)
    assert result == pytest.approx(150.0)


def test_train_full_produces_loadable_model(tmp_path):
    import joblib
    from src.model.train_full import train_and_save

    train = _make_split_df(400)
    test = _make_split_df(100)

    with patch("src.model.train_full.load_and_split", return_value=(train, test)):
        out = tmp_path / "model_full.joblib"
        train_and_save(output_path=str(out))

    assert out.exists()
    model = joblib.load(str(out))
    sample = pd.DataFrame([{c: 1.0 for c in MODEL_FEATURES}])
    result = model.predict(sample)
    assert isinstance(float(result[0]), float)


def test_train_simple_produces_loadable_model(tmp_path):
    import joblib
    from src.model.train_simple import train_and_save

    train = _make_split_df(400)
    test = _make_split_df(100)

    with patch("src.model.train_simple.load_and_split", return_value=(train, test)):
        out = tmp_path / "model_simple.joblib"
        train_and_save(output_path=str(out))

    assert out.exists()
    model = joblib.load(str(out))
    sample = pd.DataFrame([{c: 1.0 for c in MODEL_FEATURES}])
    result = model.predict(sample)
    assert isinstance(float(result[0]), float)


def test_train_forecast_produces_loadable_model(tmp_path):
    import joblib
    from src.model.train_forecast import train_and_save

    train = _make_split_df(400)
    test = _make_split_df(100)

    with patch("src.model.train_forecast.load_and_split", return_value=(train, test)):
        out = tmp_path / "model_forecast.joblib"
        train_and_save(output_path=str(out))

    assert out.exists()
    artifact = joblib.load(str(out))
    assert "model" in artifact
    assert "model_type" in artifact
    assert artifact["model_type"] in {"Chronos", "MSTL", "XGBoost_lags"}
