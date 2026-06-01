import pathlib

from src.model.evaluate import write_leaderboard
from src.model.train_full import train_and_save

scores = train_and_save()
print("model_full.joblib saved.")

leaderboard_path = pathlib.Path("src/model/trained/leaderboard.json")
write_leaderboard("regression", scores, "r2", leaderboard_path)
print(f"Leaderboard written to {leaderboard_path}")
