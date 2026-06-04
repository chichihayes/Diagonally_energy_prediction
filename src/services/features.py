import pandas as pd

from src.services.data_loader import MODEL_FEATURES


def build_lag_matrix(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    present = [c for c in MODEL_FEATURES if c in df.columns]
    X = df[present].copy()
    y = df["aggregate_wh"].copy()
    combined = X.join(y).dropna()
    return combined.drop("aggregate_wh", axis=1), combined["aggregate_wh"]


