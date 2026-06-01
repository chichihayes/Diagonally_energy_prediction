import pathlib

from src.model.evaluate import write_leaderboard
from src.model.train_forecast import train_and_save

scores = train_and_save()
print("model_forecast.joblib saved.")

leaderboard_path = pathlib.Path("src/model/trained/leaderboard.json")
write_leaderboard("forecast", scores, "mape", leaderboard_path)
print(f"Forecast leaderboard written to {leaderboard_path}")
