import json
import pathlib
from datetime import datetime
from fastapi import APIRouter, HTTPException, Query

from src.services import database
from src.model.forecast import forecast_24h as _forecast_24h, forecast_7d
from src.services.database import supabase

router = APIRouter(prefix="/api/v1")

_FORECAST_LEADERBOARD_PATH = pathlib.Path("src/model/trained/forecast_leaderboard.json")


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
    if not _FORECAST_LEADERBOARD_PATH.exists():
        raise HTTPException(
            status_code=503,
            detail="Leaderboard not available — run training scripts first",
        )
    return {"forecast": json.loads(_FORECAST_LEADERBOARD_PATH.read_text())}


@router.get("/forecast/24h")
async def get_forecast_24h():
    try:
        raw = _forecast_24h()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    items = [
        {
            "hour": entry["ds"],
            "predicted_wh": entry["yhat"],
            "predicted_kwh": entry["predicted_kwh"],
            "lower_wh": entry["yhat_lower"],
            "upper_wh": entry["yhat_upper"],
            "estimated_cost_gbp": entry["estimated_cost_gbp"],
        }
        for entry in raw
    ]

    peak_hour = max(items, key=lambda x: x["predicted_wh"])["hour"]
    lowest_hour = min(items, key=lambda x: x["predicted_wh"])["hour"]

    return {"forecast": items, "peak_hour": peak_hour, "lowest_hour": lowest_hour}


@router.get("/forecast/7d")
def get_forecast_7d():
    try:
        result = forecast_7d()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    return {
        "forecast": result["forecast"],
        "peak_day": result["peak_day"],
        "lowest_day": result["lowest_day"],
        "projected_week_bill": result["projected_week_bill"],
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
            .select("timestamp,old_mape,new_mape,model_replaced,rows_used")
            .order("timestamp", desc=True)
            .limit(1)
            .execute()
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    if not result.data:
        raise HTTPException(status_code=404, detail="No retraining has run yet")
    return result.data[0]
