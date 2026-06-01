from datetime import datetime

from fastapi import APIRouter, Query
from pydantic import BaseModel

from src.services import database
from src.services.weather import get_weather
from src.services.features import assemble_simple_features, assemble_full_features
from src.model.predict import predict_simple, predict_full
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


class FullPredictRequest(BaseModel):
    lights: int
    T1: float;  RH_1: float
    T2: float;  RH_2: float
    T3: float;  RH_3: float
    T4: float;  RH_4: float
    T5: float;  RH_5: float
    T6: float;  RH_6: float
    T7: float;  RH_7: float
    T8: float;  RH_8: float
    T9: float;  RH_9: float
    location: str


@router.post("/predict/full")
def predict_full_endpoint(body: FullPredictRequest):
    weather = get_weather(body.location)
    body_dict = body.dict(exclude={"location"})
    lights = body_dict.pop("lights")
    features = assemble_full_features(lights, body_dict, weather)
    predicted_wh = predict_full(features)
    predicted_kwh, estimated_cost_ngn = wh_to_cost(predicted_wh)
    insert_prediction({
        "tier": "full",
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
    }


@router.get("/predictions")
def get_predictions_route(
    tier: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=50),
    since: datetime | None = Query(default=None),
):
    since_str = since.isoformat() if since is not None else None
    return database.get_predictions(tier=tier, limit=limit, since=since_str)
