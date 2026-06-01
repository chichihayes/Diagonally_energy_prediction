# Diagonally Energy Prediction

ML system for real-time electricity consumption prediction via REST API.

## Stack
- Model: scikit-learn (Random Forest / XGBoost)
- API: FastAPI
- Dataset: UCI ElectricityLoadDiagrams 2011-2014

## Setup
```bash
python -m venv venv
venv\Scripts\activate       # Windows
pip install -r requirements.txt
cp .env.example .env
```

## Train the model
```bash
python scripts/run_training.py
```

## Run the API
```bash
uvicorn src.api.main:app --reload
```

## Test
```bash
pytest tests/
```

## Predict (example)
```bash
curl -X POST http://localhost:8000/api/v1/predict \
  -H "Content-Type: application/json" \
  -d '{"hour":14,"day_of_week":2,"month":6,"is_weekend":0,"lag_1h":0.45,"lag_24h":0.50,"lag_168h":0.48,"rolling_mean_3h":0.47,"rolling_mean_24h":0.49}'
```
