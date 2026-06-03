import json
import pytest
from unittest.mock import MagicMock, patch
from fastapi import HTTPException


def test_get_readings_returns_200(client, mock_get_readings):
    mock_get_readings.return_value = []
    response = client.get("/api/v1/readings")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_readings_limit_param(client, mock_get_readings):
    mock_get_readings.return_value = []
    response = client.get("/api/v1/readings?limit=5")
    assert response.status_code == 200
    mock_get_readings.assert_called_once_with(limit=5, since=None)


def test_get_readings_limit_max_50(client, mock_get_readings):
    mock_get_readings.return_value = []
    response = client.get("/api/v1/readings?limit=100")
    assert response.status_code == 422


def test_get_readings_response_shape(client, mock_get_readings):
    mock_get_readings.return_value = [
        {
            "timestamp": "2013-12-16T10:00:00",
            "aggregate_wh": 523.1,
            "fridge_wh": 74.2,
            "estimated_cost_gbp": 0.18,
        }
    ]
    response = client.get("/api/v1/readings")
    item = response.json()[0]
    assert "aggregate_wh" in item
    assert "estimated_cost_gbp" in item


def test_get_readings_since_forwarded(client, mock_get_readings):
    mock_get_readings.return_value = []
    response = client.get("/api/v1/readings?since=2013-12-16T10%3A00%3A00Z")
    assert response.status_code == 200
    mock_get_readings.assert_called_once_with(
        limit=20, since="2013-12-16T10:00:00+00:00"
    )


def test_get_readings_since_default_none(client, mock_get_readings):
    mock_get_readings.return_value = []
    response = client.get("/api/v1/readings")
    assert response.status_code == 200
    mock_get_readings.assert_called_once_with(limit=20, since=None)


def test_get_readings_invalid_since_returns_422(client):
    response = client.get("/api/v1/readings?since=not-a-date")
    assert response.status_code == 422


_MOCK_BILL_INLINE = {
    "optimistic_gbp": 45.00,
    "most_likely_gbp": 62.00,
    "pessimistic_gbp": 82.00,
    "period": "7 days",
}

_MOCK_FORECAST_7D_INLINE = {
    "forecast": [
        {
            "date": "2013-12-17",
            "predicted_wh": 6000.0,
            "predicted_kwh": 6.0,
            "lower_wh": 4000.0,
            "upper_wh": 8000.0,
            "estimated_cost_gbp": 2.04,
        }
    ] * 7,
    "peak_day": "Monday",
    "lowest_day": "Sunday",
    "projected_week_bill": _MOCK_BILL_INLINE,
}


def test_forecast_7d_valid_returns_200():
    from src.api.main import app
    from fastapi.testclient import TestClient
    from unittest.mock import patch
    client = TestClient(app)
    with patch("src.api.routes.forecast_7d", return_value=_MOCK_FORECAST_7D_INLINE):
        response = client.get("/api/v1/forecast/7d")
    assert response.status_code == 200


def test_forecast_7d_response_has_required_keys():
    from src.api.main import app
    from fastapi.testclient import TestClient
    from unittest.mock import patch
    client = TestClient(app)
    with patch("src.api.routes.forecast_7d", return_value=_MOCK_FORECAST_7D_INLINE):
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
    from unittest.mock import patch
    client = TestClient(app)
    with patch("src.api.routes.forecast_7d", side_effect=Exception("model crashed")):
        response = client.get("/api/v1/forecast/7d")
    assert response.status_code == 500


# ── GET /api/v1/forecast/24h ──────────────────────────────────────────────────

_MOCK_FORECAST_24H = [
    {
        "ds": f"2013-12-16T{h:02d}:00:00",
        "yhat": float(100 + h * 10),
        "yhat_lower": float(80 + h * 10),
        "yhat_upper": float(120 + h * 10),
        "predicted_kwh": round((100 + h * 10) / 1000, 3),
        "estimated_cost_gbp": round((100 + h * 10) / 1000 * 0.34, 2),
    }
    for h in range(24)
]


@pytest.fixture
def mock_forecast_24h():
    with patch("src.api.routes._forecast_24h", return_value=_MOCK_FORECAST_24H) as m:
        yield m


def test_forecast_24h_valid_returns_200(client, mock_forecast_24h):
    resp = client.get("/api/v1/forecast/24h")
    assert resp.status_code == 200


def test_forecast_24h_forecast_array_has_24_elements(client, mock_forecast_24h):
    resp = client.get("/api/v1/forecast/24h")
    assert len(resp.json()["forecast"]) == 24


def test_forecast_24h_each_item_has_required_fields(client, mock_forecast_24h):
    resp = client.get("/api/v1/forecast/24h")
    required = {"hour", "predicted_wh", "predicted_kwh", "lower_wh", "upper_wh", "estimated_cost_gbp"}
    for item in resp.json()["forecast"]:
        assert set(item.keys()) == required


def test_forecast_24h_peak_hour_is_highest_predicted_wh(client, mock_forecast_24h):
    resp = client.get("/api/v1/forecast/24h")
    data = resp.json()
    max_item = max(data["forecast"], key=lambda x: x["predicted_wh"])
    assert data["peak_hour"] == max_item["hour"]


def test_forecast_24h_lowest_hour_is_lowest_predicted_wh(client, mock_forecast_24h):
    resp = client.get("/api/v1/forecast/24h")
    data = resp.json()
    min_item = min(data["forecast"], key=lambda x: x["predicted_wh"])
    assert data["lowest_hour"] == min_item["hour"]


def test_forecast_24h_model_error_returns_500(client):
    with patch("src.api.routes._forecast_24h", side_effect=RuntimeError("model failed")):
        resp = client.get("/api/v1/forecast/24h")
        assert resp.status_code == 500


_MOCK_7D_FORECAST = [
    {
        "date": f"2013-12-1{i+7}",
        "predicted_wh": 6000.0 + i * 200,
        "predicted_kwh": round((6000.0 + i * 200) / 1000, 6),
        "lower_wh": 4000.0 + i * 200,
        "upper_wh": 8000.0 + i * 200,
        "estimated_cost_gbp": round((6000.0 + i * 200) / 1000 * 0.34, 2),
    }
    for i in range(7)
]

_MOCK_BILL = {
    "optimistic_gbp": 45.00,
    "most_likely_gbp": 62.00,
    "pessimistic_gbp": 82.00,
    "period": "7 days",
}

_MOCK_FORECAST_7D_RESULT = {
    "forecast": _MOCK_7D_FORECAST,
    "peak_day": "Sunday",
    "lowest_day": "Monday",
    "projected_week_bill": _MOCK_BILL,
}


def test_forecast_7d_returns_200_with_7_element_array():
    from src.api.main import app
    from fastapi.testclient import TestClient
    from unittest.mock import patch
    client = TestClient(app)
    with patch("src.api.routes.forecast_7d", return_value=_MOCK_FORECAST_7D_RESULT):
        response = client.get("/api/v1/forecast/7d")
    assert response.status_code == 200
    assert len(response.json()["forecast"]) == 7


def test_forecast_7d_bill_fields_all_present():
    from src.api.main import app
    from fastapi.testclient import TestClient
    from unittest.mock import patch
    client = TestClient(app)
    with patch("src.api.routes.forecast_7d", return_value=_MOCK_FORECAST_7D_RESULT):
        response = client.get("/api/v1/forecast/7d")
    bill = response.json()["projected_week_bill"]
    assert {"optimistic_gbp", "most_likely_gbp", "pessimistic_gbp", "period"}.issubset(bill.keys())


def test_forecast_7d_bill_ordering_holds():
    from src.api.main import app
    from fastapi.testclient import TestClient
    from unittest.mock import patch
    client = TestClient(app)
    with patch("src.api.routes.forecast_7d", return_value=_MOCK_FORECAST_7D_RESULT):
        response = client.get("/api/v1/forecast/7d")
    bill = response.json()["projected_week_bill"]
    assert bill["optimistic_gbp"] <= bill["most_likely_gbp"] <= bill["pessimistic_gbp"]


# ── GET /api/v1/models/leaderboard ───────────────────────────────────────────

_FORECAST_LEADERBOARD = [
    {"model": "Chronos",      "mape": 0.08, "winner": True},
    {"model": "MSTL",         "mape": 0.10, "winner": False},
    {"model": "XGBoost_lags", "mape": 0.12, "winner": False},
]


def test_get_leaderboard_returns_200_with_forecast_key(tmp_path):
    from fastapi.testclient import TestClient
    from src.api.main import app
    import pathlib

    lb_file = tmp_path / "forecast_leaderboard.json"
    lb_file.write_text(json.dumps(_FORECAST_LEADERBOARD))

    client = TestClient(app)
    with patch("src.api.routes._FORECAST_LEADERBOARD_PATH", lb_file):
        response = client.get("/api/v1/models/leaderboard")

    assert response.status_code == 200
    data = response.json()
    assert "forecast" in data


def test_get_leaderboard_forecast_has_exactly_one_winner(tmp_path):
    from fastapi.testclient import TestClient
    from src.api.main import app

    lb_file = tmp_path / "forecast_leaderboard.json"
    lb_file.write_text(json.dumps(_FORECAST_LEADERBOARD))

    client = TestClient(app)
    with patch("src.api.routes._FORECAST_LEADERBOARD_PATH", lb_file):
        response = client.get("/api/v1/models/leaderboard")

    data = response.json()
    assert sum(1 for e in data["forecast"] if e["winner"]) == 1


def test_get_leaderboard_returns_503_when_leaderboard_file_absent(tmp_path):
    from fastapi.testclient import TestClient
    from src.api.main import app

    missing_path = tmp_path / "nonexistent.json"

    client = TestClient(app)
    with patch("src.api.routes._FORECAST_LEADERBOARD_PATH", missing_path):
        response = client.get("/api/v1/models/leaderboard")

    assert response.status_code == 503
    assert "run training scripts" in response.json()["detail"].lower()
