import os

import joblib
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from src.services import database
from src.services.weather import get_weather

router = APIRouter(prefix="/api/v1")

_simple_model = None


def _get_simple_model():
    global _simple_model
    if _simple_model is None:
        path = os.getenv("MODEL_SIMPLE_PATH", "src/model/trained/model_simple.joblib")
        if not os.path.exists(path):
            raise HTTPException(
                status_code=503,
                detail="Simple model not trained yet. Run scripts/run_training_simple.py first.",
            )
        _simple_model = joblib.load(path)
    return _simple_model


class SimplePredictRequest(BaseModel):
    lights: float = Field(..., ge=0, description="Lights energy usage in Wh")
    T1: float = Field(..., ge=-20, le=60, description="Room temperature in °C")
    location: str = Field(..., min_length=1, description="City name for weather lookup")


@router.post("/predict/simple")
def predict_simple(payload: SimplePredictRequest):
    weather = get_weather(payload.location)
    model = _get_simple_model()
    features = [[
        payload.lights,
        payload.T1,
        weather["T_out"],
        weather["RH_out"],
        weather["Windspeed"],
        weather["Visibility"],
        weather["Tdewpoint"],
    ]]
    predicted_wh = round(float(model.predict(features)[0]), 2)
    predicted_kwh = round(predicted_wh / 1000, 4)
    tariff = float(os.getenv("ELECTRICITY_TARIFF_NGN_PER_KWH", "68.00"))
    estimated_cost_ngn = round(predicted_kwh * tariff, 2)
    return {
        "predicted_wh": predicted_wh,
        "predicted_kwh": predicted_kwh,
        "estimated_cost_ngn": estimated_cost_ngn,
        "weather_factors": weather,
    }


@router.get("/predictions")
def get_predictions_route(
    tier: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=50),
):
    return database.get_predictions(tier=tier, limit=limit)
