import pandas as pd

from src.services.data_loader import MODEL_FEATURES

_LAG_COLS = [
    "lag_1", "lag_6", "lag_144", "lag_1008",
    "rolling_mean_6", "rolling_mean_144", "rolling_std_6",
]


def build_lag_matrix(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    """Extract lag/rolling features and aggregate_wh target from a preprocessed df."""
    present = [c for c in _LAG_COLS if c in df.columns]
    X = df[present].copy()
    y = df["aggregate_wh"].copy()
    combined = X.join(y).dropna()
    return combined.drop("aggregate_wh", axis=1), combined["aggregate_wh"]


