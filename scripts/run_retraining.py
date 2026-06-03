import pandas as pd

from src.services.data_loader import MODEL_FEATURES
from src.services.database import fetch_clean_rows
from src.model.evaluate import train_all_models

_TARGET = "aggregate_wh"
_TRAIN_RATIO = 0.80
_TRAIN_PATH = "data/processed/train.csv"


def _load_base_data() -> pd.DataFrame:
    return pd.read_csv(_TRAIN_PATH, index_col=0, parse_dates=True)


def run_retraining() -> dict:
    base_df = _load_base_data()
    raw_supabase = fetch_clean_rows()
    clean_rows = [r for r in raw_supabase if not r.get("low_confidence", True)]

    if clean_rows:
        supabase_df = pd.DataFrame(
            [r["input_features"] for r in clean_rows]
        )
        supabase_df[_TARGET] = [r.get("aggregate_wh", r.get("predicted_wh", 0)) for r in clean_rows]
        combined = pd.concat([base_df, supabase_df], ignore_index=True)
    else:
        combined = base_df.copy()

    rows_used = len(combined)

    X = combined[[c for c in MODEL_FEATURES if c in combined.columns]]
    y = combined[_TARGET]

    split = int(len(X) * _TRAIN_RATIO)
    X_train, X_test = X.iloc[:split], X.iloc[split:]
    y_train, y_test = y.iloc[:split], y.iloc[split:]

    best_model, new_r2 = train_all_models(X_train, y_train, X_test, y_test)
    return {"best_model": best_model, "new_r2": float(new_r2), "rows_used": rows_used}
