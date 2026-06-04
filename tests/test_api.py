import json
import pytest
from unittest.mock import patch
from fastapi import HTTPException


_MOCK_BILL = {
    "optimistic_gbp":  45.00,
    "most_likely_gbp": 62.00,
    "pessimistic_gbp": 82.00,
    "period":          "7 days",
}

_MOCK_FORECAST_7D = {
    "forecast": [
        {
            "date":               "2013-12-17",
            "predicted_wh":       6000.0,
            "predicted_kwh":      6.0,
            "lower_wh":           4000.0,
            "upper_wh":           8000.0,
            "estimated_cost_gbp": 2.04,
        }
    ] * 7,
    "peak_day":            "Monday",
    "lowest_day":          "Sunday",
    "projected_week_bill": _MOCK_BILL,
}


def test_forecast_7d_valid_returns_200():
    from src.api.main import app
    from fastapi.testclient import TestClient
    client = TestClient(app)
    with patch("src.api.routes.forecast_7d", return_value=_MOCK_FORECAST_7D):
        response = client.get("/api/v1/forecast/7d")
    assert response.status_code == 200


def test_forecast_7d_response_has_required_keys():
    from src.api.main import app
    from fastapi.testclient import TestClient
    client = TestClient(app)
    with patch("src.api.routes.forecast_7d", return_value=_MOCK_FORECAST_7D):
        response = client.get("/api/v1/forecast/7d")
    data = response.json()
    assert set(data.keys()) == {"forecast", "peak_day", "lowest_day", "projected_week_bill"}
    assert len(data["forecast"]) == 7
    assert set(data["projected_week_bill"].keys()) == {
        "optimistic_gbp", "most_likely_gbp", "pessimistic_gbp", "period"
    }



def test_forecast_7d_model_error_returns_500():
    from src.api.main import app
    from fastapi.testclient import TestClient
    client = TestClient(app)
    with patch("src.api.routes.forecast_7d", side_effect=Exception("model crashed")):
        response = client.get("/api/v1/forecast/7d")
    assert response.status_code == 500


def test_forecast_7d_bill_ordering_holds():
    from src.api.main import app
    from fastapi.testclient import TestClient
    client = TestClient(app)
    with patch("src.api.routes.forecast_7d", return_value=_MOCK_FORECAST_7D):
        response = client.get("/api/v1/forecast/7d")
    bill = response.json()["projected_week_bill"]
    assert bill["optimistic_gbp"] <= bill["most_likely_gbp"] <= bill["pessimistic_gbp"]


