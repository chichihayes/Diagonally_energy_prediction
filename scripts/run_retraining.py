import pandas as pd

from src.services.data_loader import load_uci_csv
from src.services.database import fetch_clean_rows
from src.model.evaluate import train_all_models

_TARGET = "Appliances"
_DROP_COLS = ["rv1", "rv2", "date"]
_TRAIN_RATIO = 0.80


def run_retraining() -> dict:
    uci_df = load_uci_csv()
    raw_supabase = fetch_clean_rows()
    clean_rows = [r for r in raw_supabase if not r.get("low_confidence", True)]

    if clean_rows:
        supabase_df = pd.DataFrame(
            [r["input_features"] for r in clean_rows]
        )
        supabase_df[_TARGET] = [r.get("predicted_wh", 0) for r in clean_rows]
        combined = pd.concat([uci_df, supabase_df], ignore_index=True)
    else:
        combined = uci_df.copy()

    rows_used = len(combined)
    combined = combined.drop(columns=[c for c in _DROP_COLS if c in combined.columns])

    X = combined.drop(columns=[_TARGET], errors="ignore")
    y = combined[_TARGET]

    split = int(len(X) * _TRAIN_RATIO)
    X_train, X_test = X.iloc[:split], X.iloc[split:]
    y_train, y_test = y.iloc[:split], y.iloc[split:]

    best_model, new_r2 = train_all_models(X_train, y_train, X_test, y_test)
    return {"best_model": best_model, "new_r2": float(new_r2), "rows_used": rows_used}
