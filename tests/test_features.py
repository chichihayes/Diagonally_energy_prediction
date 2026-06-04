import pandas as pd
import numpy as np
import pytest

from src.services.data_loader import MODEL_FEATURES, APPLIANCE_COLS


def _make_preprocessed_df(n: int = 200) -> pd.DataFrame:
    """Minimal daily dataframe that mirrors what load_and_split() returns."""
    rng = np.random.default_rng(42)
    idx = pd.date_range("2013-10-09", periods=n, freq="D")
    df  = pd.DataFrame(index=idx)
    for col in APPLIANCE_COLS:
        df[col] = rng.uniform(0, 10000, n)
    df["aggregate_wh"] = df[APPLIANCE_COLS].sum(axis=1)
    df["day_of_week"]  = df.index.dayofweek
    df["month"]        = df.index.month
    df["is_weekend"]   = (df.index.dayofweek >= 5).astype(int)
    agg = df["aggregate_wh"]
    df["lag_1"]          = agg.shift(1)
    df["lag_7"]          = agg.shift(7)
    df["rolling_mean_7"] = agg.shift(1).rolling(7).mean()
    heater = df["ElectricHeater"]
    df["heater_lag_1"]          = heater.shift(1)
    df["heater_lag_7"]          = heater.shift(7)
    df["heater_rolling_mean_7"] = heater.shift(1).rolling(7).mean()
    df["temp_mean_c"] = rng.uniform(2.0, 18.0, n)
    df["temp_min_c"]  = df["temp_mean_c"] - rng.uniform(1.0, 4.0, n)
    return df.dropna()


def test_build_lag_matrix_returns_correct_columns():
    from src.services.features import build_lag_matrix
    df = _make_preprocessed_df()
    X, y = build_lag_matrix(df)
    assert list(X.columns) == MODEL_FEATURES


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
    assert "day_of_week"            in MODEL_FEATURES
    assert "month"                  in MODEL_FEATURES
    assert "is_weekend"             in MODEL_FEATURES
    assert "lag_1"                  in MODEL_FEATURES
    assert "lag_7"                  in MODEL_FEATURES
    assert "rolling_mean_7"         in MODEL_FEATURES
    assert "heater_lag_1"           in MODEL_FEATURES
    assert "heater_lag_7"           in MODEL_FEATURES
    assert "heater_rolling_mean_7"  in MODEL_FEATURES
    assert "temp_mean_c"            in MODEL_FEATURES
    assert "temp_min_c"             in MODEL_FEATURES
    assert len(MODEL_FEATURES) == 11


def test_appliance_cols_has_9_entries():
    assert len(APPLIANCE_COLS) == 9
    assert "Fridge"        in APPLIANCE_COLS
    assert "ElectricHeater" in APPLIANCE_COLS
