import json
import os
import pathlib
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from src.services import database
from src.services.weather import get_weather
from src.services.features import assemble_simple_features, assemble_full_features
from src.model.predict import predict_simple, predict_full
from src.model.forecast import forecast_24h as _forecast_24h, forecast_7d
from src.services.cost import wh_to_cost, project_monthly_bill
from src.services.database import insert_prediction, store_anomaly, supabase
from src.services.monitor import check_anomaly

router = APIRouter(prefix="/api/v1")


class SimplePredictRequest(BaseModel):
    lights: int
    T1: float
    location: str


@router.post("/predict/simple")
def predict_simple_endpoint(body: SimplePredictRequest):
    weather = get_weather(body.location)
    features = assemble_simple_features(body.lights, body.T1, weather)
    anomaly_result = check_anomaly(features)
    if anomaly_result["is_anomaly"]:
        store_anomaly({
            "timestamp": datetime.utcnow().isoformat(),
            "tier": "simple",
            "input_features": features,
            "z_scores": anomaly_result["z_scores"],
            "flagged_features": anomaly_result["flagged_features"],
            "low_confidence_prediction": True,
        })
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
        "low_confidence": anomaly_result["is_anomaly"],
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
    anomaly_result = check_anomaly(features)
    if anomaly_result["is_anomaly"]:
        store_anomaly({
            "timestamp": datetime.utcnow().isoformat(),
            "tier": "full",
            "input_features": features,
            "z_scores": anomaly_result["z_scores"],
            "flagged_features": anomaly_result["flagged_features"],
            "low_confidence_prediction": True,
        })
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
        "low_confidence": anomaly_result["is_anomaly"],
    }


@router.get("/predictions")
def get_predictions_route(
    tier: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=50),
    since: datetime | None = Query(default=None),
):
    since_str = since.isoformat() if since is not None else None
    return database.get_predictions(tier=tier, limit=limit, since=since_str)


@router.get("/models/leaderboard")
def get_leaderboard():
    model_path = os.environ.get("MODEL_PATH_FULL", "src/model/trained/model_full.joblib")
    leaderboard_path = pathlib.Path(model_path).parent / "leaderboard.json"
    if not leaderboard_path.exists():
        raise HTTPException(
            status_code=503,
            detail="Leaderboard not available — run training scripts first",
        )
    return json.loads(leaderboard_path.read_text())


@router.get("/forecast/24h")
async def get_forecast_24h(location: Optional[str] = None):
    if not location:
        raise HTTPException(status_code=400, detail="location is required")
    try:
        raw = _forecast_24h(location)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    items = [
        {
            "hour": entry["ds"],
            "predicted_wh": entry["yhat"],
            "predicted_kwh": entry["predicted_kwh"],
            "lower_wh": entry["yhat_lower"],
            "upper_wh": entry["yhat_upper"],
            "estimated_cost_ngn": entry["estimated_cost_ngn"],
        }
        for entry in raw
    ]

    peak_hour = max(items, key=lambda x: x["predicted_wh"])["hour"]
    lowest_hour = min(items, key=lambda x: x["predicted_wh"])["hour"]

    return {"forecast": items, "peak_hour": peak_hour, "lowest_hour": lowest_hour}


@router.get("/forecast/7d")
def get_forecast_7d(location: str = None):
    if not location:
        raise HTTPException(status_code=400, detail="location query param is required")
    try:
        result = forecast_7d()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    bill = project_monthly_bill(result["forecast"])
    return {
        "forecast": result["forecast"],
        "peak_day": result["peak_day"],
        "lowest_day": result["lowest_day"],
        "projected_month_bill": bill,
    }


@router.get("/monitor/drift")
def get_drift_status():
    try:
        event = database.get_latest_drift_event()
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to retrieve drift status")
    if event is None:
        raise HTTPException(status_code=404, detail="No drift check has been run yet")
    return event


@router.get("/monitor/retrain")
def get_retrain_status():
    try:
        result = (
            supabase.table("retrain_log")
            .select("timestamp,old_model_r2,new_model_r2,model_replaced,rows_used")
            .order("timestamp", desc=True)
            .limit(1)
            .execute()
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    if not result.data:
        raise HTTPException(status_code=404, detail="No retraining has run yet")
    return result.data[0]
