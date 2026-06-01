from fastapi import APIRouter, Query
from pydantic import BaseModel

from src.services import database
from src.services.weather import get_weather
from src.services.features import assemble_simple_features
from src.model.predict import predict_simple
from src.services.cost import wh_to_cost
from src.services.database import insert_prediction

router = APIRouter(prefix="/api/v1")


class SimplePredictRequest(BaseModel):
    lights: int
    T1: float
    location: str


@router.post("/predict/simple")
def predict_simple_endpoint(body: SimplePredictRequest):
    weather = get_weather(body.location)
    features = assemble_simple_features(body.lights, body.T1, weather)
    predicted_wh = predict_simple(features)
    predicted_kwh, estimated_cost_ngn = wh_to_cost(predicted_wh)
    insert_prediction({
        "tier": "simple",
        "predicted_wh": predicted_wh,
        "predicted_kwh": predicted_kwh,
        "estimated_cost_ngn": estimated_cost_ngn,
        "location": body.location,
        "input_features": features,
    })
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
