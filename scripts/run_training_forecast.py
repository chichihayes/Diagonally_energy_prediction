from src.model.train_forecast import train_and_save

scores = train_and_save()
print("model_forecast.joblib saved.")
print("forecast_leaderboard.json saved.")
for model, mape in scores.items():
    print(f"  {model}: MAPE={mape:.2f}%")
