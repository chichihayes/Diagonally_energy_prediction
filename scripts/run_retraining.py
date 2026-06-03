import pandas as pd


def run_retraining(clean_rows: pd.DataFrame) -> dict:
    from src.model.train_forecast import train_and_evaluate
    result = train_and_evaluate(extra_rows=clean_rows)
    return {
        "best_model": result["best_model"],
        "new_mape": result["best_mape"],
        "rows_used": len(clean_rows),
    }
