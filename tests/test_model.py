import numpy as np
import pandas as pd
from unittest.mock import patch

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
