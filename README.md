# Diagonally Energy Prediction

ML system for real-time electricity consumption prediction via REST API.

## Stack
- Model: scikit-learn (Random Forest / XGBoost)
- API: FastAPI
- Dataset: UCI Appliances Energy Prediction (19,735 rows, 28 features)

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
  -d '{"lights":0,"T1":19.89,"RH_1":47.6,"T2":19.2,"RH_2":44.79,"T3":19.79,"RH_3":44.73,"T_out":6.6,"Windspeed":7.0,"Visibility":63.0,"Tdewpoint":5.3}'
```
