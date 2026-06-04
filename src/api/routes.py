import json
import pathlib

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.services import database
from src.model.forecast import forecast_7d, forecast_single_day

router = APIRouter(prefix="/api/v1")

_MODEL_EVALUATION_PATH = pathlib.Path("src/model/trained/model_evaluation.json")


# ---------------------------------------------------------------------------
# Leaderboard (backend / CEO visibility)
# ---------------------------------------------------------------------------

@router.get("/models/evaluation")
def get_model_evaluation():
    if not _MODEL_EVALUATION_PATH.exists():
        raise HTTPException(
            status_code=503,
            detail="Evaluation not available — run scripts/run_training_forecast.py first",
        )
    return json.loads(_MODEL_EVALUATION_PATH.read_text())


# ---------------------------------------------------------------------------
# 7-day rolling forecast (seed-based, no user input)
# ---------------------------------------------------------------------------

@router.get("/forecast/7d")
def get_forecast_7d():
    try:
        result = forecast_7d()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    return {
        "forecast":            result["forecast"],
        "peak_day":            result["peak_day"],
        "lowest_day":          result["lowest_day"],
        "projected_week_bill": result["projected_week_bill"],
    }


# ---------------------------------------------------------------------------
# Single-day prediction from user-supplied features
# ---------------------------------------------------------------------------

class ForecastPredictRequest(BaseModel):
    date: str
    lag_1: float
    lag_7: float
    rolling_mean_7: float
    heater_lag_1: float
    heater_lag_7: float
    heater_rolling_mean_7: float
    temp_mean_c: float | None = None
    temp_min_c: float | None = None


@router.post("/forecast/predict")
def forecast_predict(body: ForecastPredictRequest):
    try:
        result = forecast_single_day(
            date_str=body.date,
            lag_1=body.lag_1,
            lag_7=body.lag_7,
            rolling_mean_7=body.rolling_mean_7,
            heater_lag_1=body.heater_lag_1,
            heater_lag_7=body.heater_lag_7,
            heater_rolling_mean_7=body.heater_rolling_mean_7,
            temp_mean_c=body.temp_mean_c,
            temp_min_c=body.temp_min_c,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    database.insert_forecast_request({
        "input_date":            result["date"],
        "lag_1":                 body.lag_1,
        "lag_7":                 body.lag_7,
        "rolling_mean_7":        body.rolling_mean_7,
        "heater_lag_1":          body.heater_lag_1,
        "heater_lag_7":          body.heater_lag_7,
        "heater_rolling_mean_7": body.heater_rolling_mean_7,
        "temp_mean_c":           result["temp_mean_c"],
        "temp_min_c":            result["temp_min_c"],
        "predicted_wh":          result["predicted_wh"],
        "predicted_kwh":         result["predicted_kwh"],
        "estimated_cost_gbp":    result["estimated_cost_gbp"],
    })

    return result
