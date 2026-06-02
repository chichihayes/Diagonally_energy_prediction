import json
import os
import pathlib

from src.model.evaluate import write_leaderboard
from src.model.train_full import train_and_save
from src.services.data_loader import load_and_split

STATS_PATH = "src/model/trained/training_stats.json"
FULL_FEATURES = [
    "lights", "T1", "RH_1", "T2", "RH_2", "T3", "RH_3", "T4", "RH_4",
    "T5", "RH_5", "T6", "RH_6", "T7", "RH_7", "T8", "RH_8", "T9", "RH_9",
    "T_out", "Press_mm_hg", "RH_out", "Windspeed", "Visibility", "Tdewpoint",
]

if not os.path.exists(STATS_PATH):
    train_df, _ = load_and_split()
    stats = {
        feat: {
            "mean": float(train_df[feat].mean()),
            "std": float(train_df[feat].std()),
        }
        for feat in FULL_FEATURES
    }
    with open(STATS_PATH, "w") as f:
        json.dump(stats, f, indent=2)
    print(f"training_stats.json saved to {STATS_PATH}")
else:
    print(f"training_stats.json already exists at {STATS_PATH} — skipping.")

scores = train_and_save()
print("model_full.joblib saved.")

leaderboard_path = pathlib.Path("src/model/trained/leaderboard.json")
write_leaderboard("regression", scores, "r2", leaderboard_path)
print(f"Leaderboard written to {leaderboard_path}")
