"""
Full training pipeline:

  Step 1 — Preprocess House_1.csv and write correct train/test splits:
              data/processed/train.csv   (all days except 9 test days)
              data/processed/test.csv    (9 strategic test days)

  Step 2 — Train RandomForest on train.csv, evaluate on test.csv, save model:
              src/model/trained/model_forecast.joblib
              src/model/trained/forecast_leaderboard.json
"""

from src.services.data_loader import save_processed_splits
from src.model.train_forecast import train_and_save

print("=" * 60)
print("Step 1 — Preprocessing and splitting data")
print("=" * 60)
save_processed_splits()

print()
print("=" * 60)
print("Step 2 — Training and evaluating model")
print("=" * 60)
scores = train_and_save()

print()
print()
print("Done. Artefacts written:")
print("    data/processed/train.csv")
print("    data/processed/test.csv")
print("    src/model/trained/model_forecast.joblib")
print("    src/model/trained/model_evaluation.json")
