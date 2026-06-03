import pandas as pd
import numpy as np
import pytest
from unittest.mock import patch

from src.services.data_loader import MODEL_FEATURES, APPLIANCE_COLS


def _make_preprocessed_df(n: int = 2000) -> pd.DataFrame:
    """Minimal preprocessed dataframe that mirrors what load_and_split() returns."""
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
    agg = df["aggregate_wh"]
    df["lag_1"] = agg.shift(1)
    df["lag_6"] = agg.shift(6)
    df["lag_144"] = agg.shift(144)
    df["lag_1008"] = agg.shift(1008)
    df["rolling_mean_6"] = agg.shift(1).rolling(6).mean()
    df["rolling_mean_144"] = agg.shift(1).rolling(144).mean()
    df["rolling_std_6"] = agg.shift(1).rolling(6).std()
    return df.dropna()


def test_build_lag_matrix_returns_correct_columns():
    from src.services.features import build_lag_matrix
    df = _make_preprocessed_df()
    X, y = build_lag_matrix(df)
    expected = ["lag_1", "lag_6", "lag_144", "lag_1008",
                "rolling_mean_6", "rolling_mean_144", "rolling_std_6"]
    assert list(X.columns) == expected


def test_build_lag_matrix_target_is_aggregate_wh():
    from src.services.features import build_lag_matrix
    df = _make_preprocessed_df()
    X, y = build_lag_matrix(df)
    assert y.name == "aggregate_wh"


def test_build_lag_matrix_has_no_nulls():
    from src.services.features import build_lag_matrix
    df = _make_preprocessed_df()
    X, y = build_lag_matrix(df)
    assert X.isna().sum().sum() == 0
    assert y.isna().sum() == 0


def test_build_lag_matrix_x_and_y_same_length():
    from src.services.features import build_lag_matrix
    df = _make_preprocessed_df()
    X, y = build_lag_matrix(df)
    assert len(X) == len(y)


def test_model_features_has_correct_names():
    assert "hour" in MODEL_FEATURES
    assert "is_night" in MODEL_FEATURES
    assert "is_peak_hour" in MODEL_FEATURES
    assert "lag_1" in MODEL_FEATURES
    assert "lag_1008" in MODEL_FEATURES
    assert "rolling_std_6" in MODEL_FEATURES
    assert len(MODEL_FEATURES) == 13


def test_appliance_cols_has_9_entries():
    assert len(APPLIANCE_COLS) == 9
    assert "Fridge" in APPLIANCE_COLS
    assert "ElectricHeater" in APPLIANCE_COLS
