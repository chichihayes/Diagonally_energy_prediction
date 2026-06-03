import pytest
from unittest.mock import MagicMock, patch
from fastapi import HTTPException


def test_get_predictions_returns_200(client, mock_get_predictions):
    mock_get_predictions.return_value = []
    response = client.get("/api/v1/predictions")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_predictions_tier_filter(client, mock_get_predictions):
    mock_get_predictions.return_value = [
        {"id": "a", "tier": "full", "predicted_wh": 60.0, "predicted_kwh": 0.06,
         "estimated_cost_gbp": 0.02, "created_at": "2013-12-16T10:00:00Z"}
    ]
    response = client.get("/api/v1/predictions?tier=full")
    assert response.status_code == 200
    mock_get_predictions.assert_called_once_with(tier="full", limit=20, since=None)


def test_get_predictions_limit_param(client, mock_get_predictions):
    mock_get_predictions.return_value = []
    response = client.get("/api/v1/predictions?limit=5")
    assert response.status_code == 200
    mock_get_predictions.assert_called_once_with(tier=None, limit=5, since=None)


def test_get_predictions_limit_max_50(client, mock_get_predictions):
    mock_get_predictions.return_value = []
    response = client.get("/api/v1/predictions?limit=100")
    assert response.status_code == 422


def test_get_predictions_response_shape(client, mock_get_predictions):
    mock_get_predictions.return_value = [
        {"id": "uuid-1", "tier": "full", "predicted_wh": 60.5,
         "predicted_kwh": 0.0605, "estimated_cost_gbp": 0.02,
         "created_at": "2013-12-16T10:00:00Z"}
    ]
    response = client.get("/api/v1/predictions")
    item = response.json()[0]
    assert "predicted_wh" in item
    assert "estimated_cost_gbp" in item
    assert "estimated_cost_ngn" not in item


@pytest.fixture
def seed_full_prediction(monkeypatch):
    row = {
        "id": "abc-123",
        "tier": "full",
        "predicted_wh": 84.3,
        "predicted_kwh": 0.0843,
        "estimated_cost_gbp": 0.03,
        "created_at": "2013-12-16T10:00:00Z",
        "input_features": {
            "hour": 10, "day_of_week": 0, "month": 12,
            "is_weekend": 0, "is_night": 0, "is_peak_hour": 0,
            "lag_1": 80.0, "lag_6": 75.0, "lag_144": 82.0, "lag_1008": 78.0,
            "rolling_mean_6": 79.0, "rolling_mean_144": 80.5, "rolling_std_6": 3.2,
        },
    }
    mock_client = MagicMock()
    chain = MagicMock()
    chain.select.return_value = chain
    chain.order.return_value = chain
    chain.limit.return_value = chain
    chain.eq.return_value = chain
    chain.execute.return_value = MagicMock(data=[row])
    mock_client.table.return_value = chain
    monkeypatch.setattr("src.services.database.supabase", mock_client)
    return row


def test_get_predictions_full_tier_includes_input_features(client, seed_full_prediction):
    resp = client.get("/api/v1/predictions?tier=full&limit=1")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 1
    record = body[0]
    assert "input_features" in record
    assert "lag_1" in record["input_features"]
    assert "hour" in record["input_features"]


def test_get_predictions_since_forwarded(client, mock_get_predictions):
    mock_get_predictions.return_value = []
    response = client.get("/api/v1/predictions?since=2013-12-16T10%3A00%3A00Z")
    assert response.status_code == 200
    mock_get_predictions.assert_called_once_with(
        tier=None, limit=20, since="2013-12-16T10:00:00+00:00"
    )


def test_get_predictions_since_default_none(client, mock_get_predictions):
    mock_get_predictions.return_value = []
    response = client.get("/api/v1/predictions")
    assert response.status_code == 200
    mock_get_predictions.assert_called_once_with(tier=None, limit=20, since=None)


def test_get_predictions_invalid_since_returns_422(client):
    response = client.get("/api/v1/predictions?since=not-a-date")
    assert response.status_code == 422


def test_forecast_7d_valid_returns_200():
    from src.api.main import app
    from fastapi.testclient import TestClient
    from unittest.mock import patch
    client = TestClient(app)
    mock_forecast_result = {
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
    }
    mock_bill = {
        "optimistic_gbp": 45.00,
        "most_likely_gbp": 62.00,
        "pessimistic_gbp": 82.00,
    }
    with patch("src.api.routes.forecast_7d", return_value=mock_forecast_result), \
         patch("src.api.routes.project_monthly_bill", return_value=mock_bill):
        response = client.get("/api/v1/forecast/7d")
    assert response.status_code == 200


def test_forecast_7d_response_has_required_keys():
    from src.api.main import app
    from fastapi.testclient import TestClient
    from unittest.mock import patch
    client = TestClient(app)
    mock_forecast_result = {
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
    }
    mock_bill = {
        "optimistic_gbp": 45.00,
        "most_likely_gbp": 62.00,
        "pessimistic_gbp": 82.00,
    }
    with patch("src.api.routes.forecast_7d", return_value=mock_forecast_result), \
         patch("src.api.routes.project_monthly_bill", return_value=mock_bill):
        response = client.get("/api/v1/forecast/7d")
    data = response.json()
    assert set(data.keys()) == {"forecast", "peak_day", "lowest_day", "projected_month_bill"}
    assert len(data["forecast"]) == 7
    assert set(data["projected_month_bill"].keys()) == {
        "optimistic_gbp", "most_likely_gbp", "pessimistic_gbp"
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

_MOCK_FORECAST_7D_RESULT = {
    "forecast": _MOCK_7D_FORECAST,
    "peak_day": "Sunday",
    "lowest_day": "Monday",
}

_MOCK_BILL = {
    "optimistic_gbp": 45.00,
    "most_likely_gbp": 62.00,
    "pessimistic_gbp": 82.00,
}


def test_forecast_7d_returns_200_with_7_element_array():
    from src.api.main import app
    from fastapi.testclient import TestClient
    from unittest.mock import patch
    client = TestClient(app)
    with patch("src.api.routes.forecast_7d", return_value=_MOCK_FORECAST_7D_RESULT), \
         patch("src.api.routes.project_monthly_bill", return_value=_MOCK_BILL):
        response = client.get("/api/v1/forecast/7d")
    assert response.status_code == 200
    assert len(response.json()["forecast"]) == 7


def test_forecast_7d_bill_fields_all_present():
    from src.api.main import app
    from fastapi.testclient import TestClient
    from unittest.mock import patch
    client = TestClient(app)
    with patch("src.api.routes.forecast_7d", return_value=_MOCK_FORECAST_7D_RESULT), \
         patch("src.api.routes.project_monthly_bill", return_value=_MOCK_BILL):
        response = client.get("/api/v1/forecast/7d")
    bill = response.json()["projected_month_bill"]
    assert {"optimistic_gbp", "most_likely_gbp", "pessimistic_gbp"}.issubset(bill.keys())


def test_forecast_7d_bill_ordering_holds():
    from src.api.main import app
    from fastapi.testclient import TestClient
    from unittest.mock import patch
    client = TestClient(app)
    with patch("src.api.routes.forecast_7d", return_value=_MOCK_FORECAST_7D_RESULT), \
         patch("src.api.routes.project_monthly_bill", return_value=_MOCK_BILL):
        response = client.get("/api/v1/forecast/7d")
    bill = response.json()["projected_month_bill"]
    assert bill["optimistic_gbp"] <= bill["most_likely_gbp"] <= bill["pessimistic_gbp"]


# ── GET /api/v1/models/leaderboard ───────────────────────────────────────────

_LEADERBOARD = {
    "regression": [
        {"model": "RandomForest", "r2": 0.91, "winner": False},
        {"model": "XGBoost",      "r2": 0.94, "winner": True},
        {"model": "LightGBM",     "r2": 0.92, "winner": False},
        {"model": "CatBoost",     "r2": 0.90, "winner": False},
        {"model": "ExtraTrees",   "r2": 0.89, "winner": False},
        {"model": "Ridge",        "r2": 0.78, "winner": False},
    ],
    "forecast": [
        {"model": "Chronos",      "mape": 0.08, "winner": True},
        {"model": "MSTL",         "mape": 0.10, "winner": False},
        {"model": "XGBoost_lags", "mape": 0.12, "winner": False},
    ],
}


def test_get_leaderboard_returns_200_with_regression_and_forecast_keys(tmp_path):
    import json
    from unittest.mock import patch
    from fastapi.testclient import TestClient
    from src.api.main import app

    lb_file = tmp_path / "leaderboard.json"
    lb_file.write_text(json.dumps(_LEADERBOARD))
    model_path = tmp_path / "model_full.joblib"

    client = TestClient(app)
    with patch.dict("os.environ", {"MODEL_PATH_FULL": str(model_path)}):
        response = client.get("/api/v1/models/leaderboard")

    assert response.status_code == 200
    data = response.json()
    assert "regression" in data
    assert "forecast" in data


def test_get_leaderboard_regression_has_exactly_one_winner(tmp_path):
    import json
    from unittest.mock import patch
    from fastapi.testclient import TestClient
    from src.api.main import app

    (tmp_path / "leaderboard.json").write_text(json.dumps(_LEADERBOARD))
    model_path = tmp_path / "model_full.joblib"

    client = TestClient(app)
    with patch.dict("os.environ", {"MODEL_PATH_FULL": str(model_path)}):
        response = client.get("/api/v1/models/leaderboard")

    data = response.json()
    assert sum(1 for e in data["regression"] if e["winner"]) == 1


def test_get_leaderboard_forecast_has_exactly_one_winner(tmp_path):
    import json
    from unittest.mock import patch
    from fastapi.testclient import TestClient
    from src.api.main import app

    (tmp_path / "leaderboard.json").write_text(json.dumps(_LEADERBOARD))
    model_path = tmp_path / "model_full.joblib"

    client = TestClient(app)
    with patch.dict("os.environ", {"MODEL_PATH_FULL": str(model_path)}):
        response = client.get("/api/v1/models/leaderboard")

    data = response.json()
    assert sum(1 for e in data["forecast"] if e["winner"]) == 1


def test_get_leaderboard_returns_503_when_leaderboard_file_absent(tmp_path):
    from unittest.mock import patch
    from fastapi.testclient import TestClient
    from src.api.main import app

    model_path = tmp_path / "model_full.joblib"

    client = TestClient(app)
    with patch.dict("os.environ", {"MODEL_PATH_FULL": str(model_path)}):
        response = client.get("/api/v1/models/leaderboard")

    assert response.status_code == 503
    assert "run training scripts" in response.json()["detail"].lower()


# ── GET /api/v1/monitor/drift ─────────────────────────────────────────────────

def test_get_monitor_drift_returns_200_with_latest_event(client):
    mock_event = {
        "timestamp": "2013-12-16T10:00:00Z",
        "drift_detected": True,
        "drifted_features": ["lag_1"],
        "deviations": {"lag_1": 20.5},
        "clean_row_count": 100,
    }
    with patch("src.api.routes.database.get_latest_drift_event", return_value=mock_event):
        response = client.get("/api/v1/monitor/drift")
    assert response.status_code == 200
    body = response.json()
    assert body["drift_detected"] is True
    assert body["drifted_features"] == ["lag_1"]
    assert body["deviations"]["lag_1"] == 20.5
    assert body["clean_row_count"] == 100


def test_get_monitor_drift_returns_404_when_no_data(client):
    with patch("src.api.routes.database.get_latest_drift_event", return_value=None):
        response = client.get("/api/v1/monitor/drift")
    assert response.status_code == 404
    assert response.json()["detail"] == "No drift check has been run yet"


def test_get_monitor_drift_returns_500_on_db_error(client):
    with patch("src.api.routes.database.get_latest_drift_event", side_effect=Exception("db connection failed")):
        response = client.get("/api/v1/monitor/drift")
    assert response.status_code == 500
