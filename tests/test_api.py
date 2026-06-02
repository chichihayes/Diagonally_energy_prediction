import pytest
from unittest.mock import MagicMock, patch
from fastapi import HTTPException

MOCK_WEATHER = {
    "T_out": 28.4, "RH_out": 82.0,
    "Windspeed": 3.1, "Visibility": 10.0, "Tdewpoint": 25.1,
}


def test_get_predictions_returns_200(client, mock_get_predictions):
    mock_get_predictions.return_value = []
    response = client.get("/api/v1/predictions")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_predictions_tier_filter(client, mock_get_predictions):
    mock_get_predictions.return_value = [
        {"id": "a", "tier": "simple", "predicted_wh": 60.0, "predicted_kwh": 0.06,
         "estimated_cost_ngn": 4.08, "location": "Lagos", "created_at": "2026-06-01T10:00:00Z"}
    ]
    response = client.get("/api/v1/predictions?tier=simple")
    assert response.status_code == 200
    mock_get_predictions.assert_called_once_with(tier="simple", limit=20, since=None)


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
        {"id": "uuid-1", "tier": "simple", "predicted_wh": 60.5,
         "predicted_kwh": 0.0605, "estimated_cost_ngn": 4.11,
         "location": "Lagos", "created_at": "2026-06-01T10:00:00Z"}
    ]
    response = client.get("/api/v1/predictions")
    item = response.json()[0]
    assert set(item.keys()) == {"id", "tier", "predicted_wh", "predicted_kwh",
                                "estimated_cost_ngn", "location", "created_at"}


@pytest.fixture
def mock_predict_simple_deps(monkeypatch):
    weather = {"T_out": 28.4, "RH_out": 82.0, "Windspeed": 3.1, "Visibility": 10.0, "Tdewpoint": 25.1}
    monkeypatch.setattr("src.api.routes.get_weather", lambda city: weather)
    monkeypatch.setattr("src.api.routes.predict_simple", lambda features: 60.5)
    monkeypatch.setattr("src.api.routes.insert_prediction", lambda row: None)
    monkeypatch.setattr("src.api.routes.check_anomaly", lambda features: {"is_anomaly": False, "z_scores": {}, "flagged_features": []})
    monkeypatch.setattr("src.api.routes.store_anomaly", lambda record: None)
    monkeypatch.setenv("ELECTRICITY_TARIFF_NGN_PER_KWH", "68.00")
    return weather


def test_predict_simple_returns_200(client, mock_predict_simple_deps):
    response = client.post("/api/v1/predict/simple", json={"lights": 0, "T1": 19.89, "location": "Lagos"})
    assert response.status_code == 200


def test_predict_simple_response_shape(client, mock_predict_simple_deps):
    response = client.post("/api/v1/predict/simple", json={"lights": 0, "T1": 19.89, "location": "Lagos"})
    body = response.json()
    assert set(body.keys()) == {"predicted_wh", "predicted_kwh", "estimated_cost_ngn", "weather_factors", "low_confidence"}


def test_predict_simple_kwh_equals_wh_over_1000(client, mock_predict_simple_deps):
    response = client.post("/api/v1/predict/simple", json={"lights": 0, "T1": 19.89, "location": "Lagos"})
    body = response.json()
    assert body["predicted_kwh"] == pytest.approx(body["predicted_wh"] / 1000)


def test_predict_simple_cost_calculation(client, mock_predict_simple_deps):
    response = client.post("/api/v1/predict/simple", json={"lights": 0, "T1": 19.89, "location": "Lagos"})
    body = response.json()
    expected = round(body["predicted_kwh"] * 68.00, 2)
    assert body["estimated_cost_ngn"] == pytest.approx(expected)


def test_predict_simple_weather_factors_keys(client, mock_predict_simple_deps):
    response = client.post("/api/v1/predict/simple", json={"lights": 0, "T1": 19.89, "location": "Lagos"})
    wf = response.json()["weather_factors"]
    assert set(wf.keys()) == {"T_out", "RH_out", "Windspeed", "Visibility", "Tdewpoint"}


def test_predict_simple_missing_field_returns_422(client):
    response = client.post("/api/v1/predict/simple", json={"lights": 0, "T1": 19.89})
    assert response.status_code == 422


def test_predict_simple_weather_error_propagates(client, monkeypatch):
    monkeypatch.setattr("src.api.routes.get_weather", lambda city: (_ for _ in ()).throw(HTTPException(status_code=500, detail="Weather fetch failed")))
    response = client.post("/api/v1/predict/simple", json={"lights": 0, "T1": 19.89, "location": "Lagos"})
    assert response.status_code == 500


def test_predict_simple_valid_input_returns_200(client):
    with patch("src.api.routes.get_weather", return_value=MOCK_WEATHER), \
         patch("src.api.routes.predict_simple", return_value=60.5), \
         patch("src.api.routes.insert_prediction"), \
         patch("src.api.routes.check_anomaly", return_value={"is_anomaly": False, "z_scores": {}, "flagged_features": []}), \
         patch("src.api.routes.store_anomaly"):
        resp = client.post("/api/v1/predict/simple", json={
            "lights": 0, "T1": 19.89, "location": "Lagos"
        })
    assert resp.status_code == 200
    body = resp.json()
    assert "predicted_wh" in body
    assert "predicted_kwh" in body
    assert "estimated_cost_ngn" in body
    assert "weather_factors" in body
    assert body["predicted_wh"] == pytest.approx(60.5)
    assert body["predicted_kwh"] == pytest.approx(0.0605)
    assert body["weather_factors"] == MOCK_WEATHER


def test_predict_simple_unknown_city_returns_500(client):
    with patch("src.api.routes.get_weather",
               side_effect=HTTPException(status_code=500, detail="Weather fetch failed")):
        resp = client.post("/api/v1/predict/simple", json={
            "lights": 0, "T1": 19.89, "location": "UnknownXYZ"
        })
    assert resp.status_code == 500


@pytest.fixture
def seed_full_prediction(monkeypatch):
    row = {
        "id": "abc-123",
        "tier": "full",
        "predicted_wh": 84.3,
        "predicted_kwh": 0.0843,
        "estimated_cost_ngn": 7.21,
        "location": "Lagos",
        "created_at": "2026-06-01T10:00:00Z",
        "input_features": {
            "T1": 19.89, "RH_1": 47.6,
            "T2": 19.2, "RH_2": 44.79,
            "T3": 19.79, "RH_3": 44.73,
            "T4": 17.17, "RH_4": 41.67,
            "T5": 17.2, "RH_5": 55.2,
            "T6": 7.03, "RH_6": 84.26,
            "T7": 17.2, "RH_7": 41.63,
            "T8": 18.2, "RH_8": 48.9,
            "T9": 17.03, "RH_9": 45.53,
            "T_out": 28.4, "RH_out": 82.0,
            "Windspeed": 3.1, "Visibility": 10.0,
            "Tdewpoint": 25.1,
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
    assert "T1" in record["input_features"]
    assert "RH_1" in record["input_features"]
    assert "T_out" in record["input_features"]


def test_get_predictions_since_forwarded(client, mock_get_predictions):
    mock_get_predictions.return_value = []
    response = client.get("/api/v1/predictions?since=2026-05-31T10%3A00%3A00Z")
    assert response.status_code == 200
    mock_get_predictions.assert_called_once_with(
        tier=None, limit=20, since="2026-05-31T10:00:00+00:00"
    )


def test_get_predictions_since_default_none(client, mock_get_predictions):
    mock_get_predictions.return_value = []
    response = client.get("/api/v1/predictions")
    assert response.status_code == 200
    mock_get_predictions.assert_called_once_with(tier=None, limit=20, since=None)


def test_get_predictions_invalid_since_returns_422(client):
    response = client.get("/api/v1/predictions?since=not-a-date")
    assert response.status_code == 422


# ── POST /api/v1/predict/full ─────────────────────────────────────────────────

_VALID_FULL_BODY = {
    "lights": 0,
    "T1": 19.89, "RH_1": 47.6,
    "T2": 19.2,  "RH_2": 44.79,
    "T3": 19.79, "RH_3": 44.73,
    "T4": 17.17, "RH_4": 41.67,
    "T5": 17.2,  "RH_5": 55.2,
    "T6": 7.03,  "RH_6": 84.26,
    "T7": 17.2,  "RH_7": 41.63,
    "T8": 18.2,  "RH_8": 48.9,
    "T9": 17.03, "RH_9": 45.53,
    "location": "Lagos",
}

_MOCK_WEATHER_FULL = {
    "T_out": 6.6, "Press_mm_hg": 733.5, "RH_out": 92.0,
    "Windspeed": 7.0, "Visibility": 63.0, "Tdewpoint": 5.3,
}


@pytest.fixture
def mock_predict_full_deps(monkeypatch):
    monkeypatch.setattr("src.api.routes.get_weather", lambda city: _MOCK_WEATHER_FULL)
    monkeypatch.setattr("src.api.routes.predict_full", lambda features: 84.3)
    monkeypatch.setattr("src.api.routes.insert_prediction", lambda row: None)
    monkeypatch.setattr("src.api.routes.check_anomaly", lambda features: {"is_anomaly": False, "z_scores": {}, "flagged_features": []})
    monkeypatch.setattr("src.api.routes.store_anomaly", lambda record: None)
    monkeypatch.setenv("ELECTRICITY_TARIFF_NGN_PER_KWH", "68.00")


def test_predict_full_valid_body_returns_200_with_all_fields(client, mock_predict_full_deps):
    response = client.post("/api/v1/predict/full", json=_VALID_FULL_BODY)
    assert response.status_code == 200
    data = response.json()
    assert set(data.keys()) == {"predicted_wh", "predicted_kwh", "estimated_cost_ngn", "low_confidence"}
    assert data["predicted_wh"] == pytest.approx(84.3)


def test_predict_full_predicted_kwh_equals_wh_over_1000(client, mock_predict_full_deps):
    response = client.post("/api/v1/predict/full", json=_VALID_FULL_BODY)
    data = response.json()
    assert data["predicted_kwh"] == pytest.approx(data["predicted_wh"] / 1000, rel=1e-5)


def test_predict_full_estimated_cost_ngn_matches_tariff(client, mock_predict_full_deps):
    response = client.post("/api/v1/predict/full", json=_VALID_FULL_BODY)
    data = response.json()
    assert data["estimated_cost_ngn"] == round(data["predicted_kwh"] * 68.00, 2)


def test_predict_full_missing_sensor_field_returns_422(client):
    body = {k: v for k, v in _VALID_FULL_BODY.items() if k != "T3"}
    response = client.post("/api/v1/predict/full", json=body)
    assert response.status_code == 422


def test_predict_full_weather_failure_returns_500(client, monkeypatch):
    monkeypatch.setattr(
        "src.api.routes.get_weather",
        lambda city: (_ for _ in ()).throw(HTTPException(status_code=500, detail="weather unavailable")),
    )
    response = client.post("/api/v1/predict/full", json=_VALID_FULL_BODY)
    assert response.status_code == 500


def test_predict_full_calls_insert_prediction_once_with_tier_full(client, monkeypatch):
    mock_insert = MagicMock()
    monkeypatch.setattr("src.api.routes.get_weather", lambda city: _MOCK_WEATHER_FULL)
    monkeypatch.setattr("src.api.routes.predict_full", lambda features: 84.3)
    monkeypatch.setattr("src.api.routes.insert_prediction", mock_insert)
    monkeypatch.setattr("src.api.routes.check_anomaly", lambda features: {"is_anomaly": False, "z_scores": {}, "flagged_features": []})
    monkeypatch.setattr("src.api.routes.store_anomaly", lambda record: None)
    monkeypatch.setenv("ELECTRICITY_TARIFF_NGN_PER_KWH", "68.00")
    client.post("/api/v1/predict/full", json=_VALID_FULL_BODY)
    mock_insert.assert_called_once()
    row = mock_insert.call_args[0][0]
    assert row["tier"] == "full"
    assert row["location"] == "Lagos"
    assert row["predicted_wh"] == pytest.approx(84.3)


def test_forecast_7d_valid_location_returns_200():
    from src.api.main import app
    from fastapi.testclient import TestClient
    from unittest.mock import patch
    client = TestClient(app)
    mock_forecast_result = {
        "forecast": [
            {
                "date": "2026-06-01",
                "predicted_wh": 6000.0,
                "predicted_kwh": 6.0,
                "lower_wh": 4000.0,
                "upper_wh": 8000.0,
                "estimated_cost_ngn": 408.0,
            }
        ] * 7,
        "peak_day": "Monday",
        "lowest_day": "Sunday",
    }
    mock_bill = {
        "optimistic_ngn": 3200.0,
        "most_likely_ngn": 4200.0,
        "pessimistic_ngn": 5100.0,
    }
    with patch("src.api.routes.forecast_7d", return_value=mock_forecast_result), \
         patch("src.api.routes.project_monthly_bill", return_value=mock_bill):
        response = client.get("/api/v1/forecast/7d?location=Lagos")
    assert response.status_code == 200


def test_forecast_7d_response_has_required_keys():
    from src.api.main import app
    from fastapi.testclient import TestClient
    from unittest.mock import patch
    client = TestClient(app)
    mock_forecast_result = {
        "forecast": [
            {
                "date": "2026-06-01",
                "predicted_wh": 6000.0,
                "predicted_kwh": 6.0,
                "lower_wh": 4000.0,
                "upper_wh": 8000.0,
                "estimated_cost_ngn": 408.0,
            }
        ] * 7,
        "peak_day": "Monday",
        "lowest_day": "Sunday",
    }
    mock_bill = {
        "optimistic_ngn": 3200.0,
        "most_likely_ngn": 4200.0,
        "pessimistic_ngn": 5100.0,
    }
    with patch("src.api.routes.forecast_7d", return_value=mock_forecast_result), \
         patch("src.api.routes.project_monthly_bill", return_value=mock_bill):
        response = client.get("/api/v1/forecast/7d?location=Lagos")
    data = response.json()
    assert set(data.keys()) == {"forecast", "peak_day", "lowest_day", "projected_month_bill"}
    assert len(data["forecast"]) == 7
    assert set(data["projected_month_bill"].keys()) == {
        "optimistic_ngn", "most_likely_ngn", "pessimistic_ngn"
    }


def test_forecast_7d_missing_location_returns_400():
    from src.api.main import app
    from fastapi.testclient import TestClient
    client = TestClient(app)
    response = client.get("/api/v1/forecast/7d")
    assert response.status_code == 400


def test_forecast_7d_model_error_returns_500():
    from src.api.main import app
    from fastapi.testclient import TestClient
    from unittest.mock import patch
    client = TestClient(app)
    with patch("src.api.routes.forecast_7d", side_effect=Exception("model crashed")):
        response = client.get("/api/v1/forecast/7d?location=Lagos")
    assert response.status_code == 500


# ── GET /api/v1/forecast/24h ──────────────────────────────────────────────────

_MOCK_FORECAST_24H = [
    {
        "ds": f"2026-06-01T{h:02d}:00:00Z",
        "yhat": float(100 + h * 10),
        "yhat_lower": float(80 + h * 10),
        "yhat_upper": float(120 + h * 10),
        "predicted_kwh": round((100 + h * 10) / 1000, 3),
        "estimated_cost_ngn": round((100 + h * 10) / 1000 * 68.0, 2),
    }
    for h in range(24)
]


@pytest.fixture
def mock_forecast_24h():
    with patch("src.api.routes._forecast_24h", return_value=_MOCK_FORECAST_24H) as m:
        yield m


def test_forecast_24h_valid_location_returns_200(client, mock_forecast_24h):
    resp = client.get("/api/v1/forecast/24h?location=Lagos")
    assert resp.status_code == 200


def test_forecast_24h_forecast_array_has_24_elements(client, mock_forecast_24h):
    resp = client.get("/api/v1/forecast/24h?location=Lagos")
    assert len(resp.json()["forecast"]) == 24


def test_forecast_24h_each_item_has_required_fields(client, mock_forecast_24h):
    resp = client.get("/api/v1/forecast/24h?location=Lagos")
    required = {"hour", "predicted_wh", "predicted_kwh", "lower_wh", "upper_wh", "estimated_cost_ngn"}
    for item in resp.json()["forecast"]:
        assert set(item.keys()) == required


def test_forecast_24h_peak_hour_is_highest_predicted_wh(client, mock_forecast_24h):
    resp = client.get("/api/v1/forecast/24h?location=Lagos")
    data = resp.json()
    max_item = max(data["forecast"], key=lambda x: x["predicted_wh"])
    assert data["peak_hour"] == max_item["hour"]


def test_forecast_24h_lowest_hour_is_lowest_predicted_wh(client, mock_forecast_24h):
    resp = client.get("/api/v1/forecast/24h?location=Lagos")
    data = resp.json()
    min_item = min(data["forecast"], key=lambda x: x["predicted_wh"])
    assert data["lowest_hour"] == min_item["hour"]


def test_forecast_24h_missing_location_returns_400(client):
    resp = client.get("/api/v1/forecast/24h")
    assert resp.status_code == 400


def test_forecast_24h_model_error_returns_500(client):
    with patch("src.api.routes._forecast_24h", side_effect=RuntimeError("model failed")):
        resp = client.get("/api/v1/forecast/24h?location=Lagos")
        assert resp.status_code == 500


_MOCK_7D_FORECAST = [
    {
        "date": f"2026-06-0{i+1}",
        "predicted_wh": 6000.0 + i * 200,
        "predicted_kwh": round((6000.0 + i * 200) / 1000, 6),
        "lower_wh": 4000.0 + i * 200,
        "upper_wh": 8000.0 + i * 200,
        "estimated_cost_ngn": round((6000.0 + i * 200) / 1000 * 68.00, 2),
    }
    for i in range(7)
]

_MOCK_FORECAST_7D_RESULT = {
    "forecast": _MOCK_7D_FORECAST,
    "peak_day": "Sunday",
    "lowest_day": "Monday",
}

_MOCK_BILL = {
    "optimistic_ngn": 3200.00,
    "most_likely_ngn": 4200.00,
    "pessimistic_ngn": 5100.00,
}


def test_forecast_7d_valid_location_returns_200_with_7_element_array():
    from src.api.main import app
    from fastapi.testclient import TestClient
    from unittest.mock import patch
    client = TestClient(app)
    with patch("src.api.routes.forecast_7d", return_value=_MOCK_FORECAST_7D_RESULT), \
         patch("src.api.routes.project_monthly_bill", return_value=_MOCK_BILL):
        response = client.get("/api/v1/forecast/7d?location=Lagos")
    assert response.status_code == 200
    assert len(response.json()["forecast"]) == 7


def test_forecast_7d_bill_fields_all_present():
    from src.api.main import app
    from fastapi.testclient import TestClient
    from unittest.mock import patch
    client = TestClient(app)
    with patch("src.api.routes.forecast_7d", return_value=_MOCK_FORECAST_7D_RESULT), \
         patch("src.api.routes.project_monthly_bill", return_value=_MOCK_BILL):
        response = client.get("/api/v1/forecast/7d?location=Lagos")
    bill = response.json()["projected_month_bill"]
    assert {"optimistic_ngn", "most_likely_ngn", "pessimistic_ngn"}.issubset(bill.keys())


def test_forecast_7d_bill_ordering_holds():
    from src.api.main import app
    from fastapi.testclient import TestClient
    from unittest.mock import patch
    client = TestClient(app)
    with patch("src.api.routes.forecast_7d", return_value=_MOCK_FORECAST_7D_RESULT), \
         patch("src.api.routes.project_monthly_bill", return_value=_MOCK_BILL):
        response = client.get("/api/v1/forecast/7d?location=Lagos")
    bill = response.json()["projected_month_bill"]
    assert bill["optimistic_ngn"] <= bill["most_likely_ngn"] <= bill["pessimistic_ngn"]


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
        {"model": "Prophet",  "mape": 0.12, "winner": False},
        {"model": "XGBoost",  "mape": 0.08, "winner": True},
        {"model": "LightGBM", "mape": 0.10, "winner": False},
        {"model": "LSTM",     "mape": 0.11, "winner": False},
        {"model": "TFT",      "mape": 0.09, "winner": False},
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

    model_path = tmp_path / "model_full.joblib"  # leaderboard.json intentionally not created

    client = TestClient(app)
    with patch.dict("os.environ", {"MODEL_PATH_FULL": str(model_path)}):
        response = client.get("/api/v1/models/leaderboard")

    assert response.status_code == 503
    assert "run training scripts" in response.json()["detail"].lower()


# ── low_confidence flag tests ─────────────────────────────────────────────────

MOCK_WEATHER_FULL = {
    "T_out": 28.0, "Press_mm_hg": 733.0, "RH_out": 80.0,
    "Windspeed": 3.0, "Visibility": 10.0, "Tdewpoint": 25.0,
}
MOCK_WEATHER_SIMPLE = {
    "T_out": 28.0, "RH_out": 80.0,
    "Windspeed": 3.0, "Visibility": 10.0, "Tdewpoint": 25.0,
}
FULL_PAYLOAD = {
    "lights": 0, "T1": 20.0, "RH_1": 47.0, "T2": 19.0, "RH_2": 44.0,
    "T3": 19.0, "RH_3": 44.0, "T4": 17.0, "RH_4": 41.0, "T5": 17.0,
    "RH_5": 55.0, "T6": 7.0, "RH_6": 84.0, "T7": 17.0, "RH_7": 41.0,
    "T8": 18.0, "RH_8": 48.0, "T9": 17.0, "RH_9": 45.0, "location": "Lagos",
}
ANOMALY_FALSE = {"is_anomaly": False, "z_scores": {}, "flagged_features": []}
ANOMALY_TRUE  = {"is_anomaly": True,  "z_scores": {"T1": 30.1}, "flagged_features": ["T1"]}


def test_predict_full_response_contains_low_confidence_field(client):
    with patch("src.api.routes.check_anomaly", return_value=ANOMALY_FALSE), \
         patch("src.api.routes.get_weather", return_value=MOCK_WEATHER_FULL), \
         patch("src.api.routes.predict_full", return_value=84.3), \
         patch("src.api.routes.insert_prediction"):
        resp = client.post("/api/v1/predict/full", json=FULL_PAYLOAD)
    assert resp.status_code == 200
    assert "low_confidence" in resp.json()
    assert resp.json()["low_confidence"] is False


def test_predict_simple_response_contains_low_confidence_field(client):
    with patch("src.api.routes.check_anomaly", return_value=ANOMALY_FALSE), \
         patch("src.api.routes.get_weather", return_value=MOCK_WEATHER_SIMPLE), \
         patch("src.api.routes.predict_simple", return_value=60.5), \
         patch("src.api.routes.insert_prediction"):
        resp = client.post(
            "/api/v1/predict/simple",
            json={"lights": 0, "T1": 20.0, "location": "Lagos"},
        )
    assert resp.status_code == 200
    assert "low_confidence" in resp.json()
    assert resp.json()["low_confidence"] is False


def test_predict_full_anomaly_sets_low_confidence_true(client):
    with patch("src.api.routes.check_anomaly", return_value=ANOMALY_TRUE), \
         patch("src.api.routes.store_anomaly") as mock_store, \
         patch("src.api.routes.get_weather", return_value=MOCK_WEATHER_FULL), \
         patch("src.api.routes.predict_full", return_value=84.3), \
         patch("src.api.routes.insert_prediction"):
        resp = client.post("/api/v1/predict/full", json=FULL_PAYLOAD)
    assert resp.status_code == 200
    assert resp.json()["low_confidence"] is True
    mock_store.assert_called_once()


def test_predict_full_no_anomaly_does_not_call_store_anomaly(client):
    with patch("src.api.routes.check_anomaly", return_value=ANOMALY_FALSE), \
         patch("src.api.routes.store_anomaly") as mock_store, \
         patch("src.api.routes.get_weather", return_value=MOCK_WEATHER_FULL), \
         patch("src.api.routes.predict_full", return_value=84.3), \
         patch("src.api.routes.insert_prediction"):
        client.post("/api/v1/predict/full", json=FULL_PAYLOAD)
    mock_store.assert_not_called()


def test_predict_full_store_anomaly_called_with_correct_tier(client):
    with patch("src.api.routes.check_anomaly", return_value=ANOMALY_TRUE), \
         patch("src.api.routes.store_anomaly") as mock_store, \
         patch("src.api.routes.get_weather", return_value=MOCK_WEATHER_FULL), \
         patch("src.api.routes.predict_full", return_value=84.3), \
         patch("src.api.routes.insert_prediction"):
        client.post("/api/v1/predict/full", json=FULL_PAYLOAD)
    call_record = mock_store.call_args[0][0]
    assert call_record["tier"] == "full"
    assert call_record["low_confidence_prediction"] is True
    assert "z_scores" in call_record
    assert "flagged_features" in call_record
    assert "input_features" in call_record


def test_predict_simple_anomaly_sets_low_confidence_true(client):
    with patch("src.api.routes.check_anomaly", return_value=ANOMALY_TRUE), \
         patch("src.api.routes.store_anomaly") as mock_store, \
         patch("src.api.routes.get_weather", return_value=MOCK_WEATHER_SIMPLE), \
         patch("src.api.routes.predict_simple", return_value=60.5), \
         patch("src.api.routes.insert_prediction"):
        resp = client.post(
            "/api/v1/predict/simple",
            json={"lights": 0, "T1": 20.0, "location": "Lagos"},
        )
    assert resp.status_code == 200
    assert resp.json()["low_confidence"] is True
    call_record = mock_store.call_args[0][0]
    assert call_record["tier"] == "simple"
    assert call_record["low_confidence_prediction"] is True


def test_predict_simple_no_anomaly_does_not_call_store_anomaly(client):
    with patch("src.api.routes.check_anomaly", return_value=ANOMALY_FALSE), \
         patch("src.api.routes.store_anomaly") as mock_store, \
         patch("src.api.routes.get_weather", return_value=MOCK_WEATHER_SIMPLE), \
         patch("src.api.routes.predict_simple", return_value=60.5), \
         patch("src.api.routes.insert_prediction"):
        client.post(
            "/api/v1/predict/simple",
            json={"lights": 0, "T1": 20.0, "location": "Lagos"},
        )
    mock_store.assert_not_called()


# ── GET /api/v1/monitor/drift ─────────────────────────────────────────────────

def test_get_monitor_drift_returns_200_with_latest_event(client):
    mock_event = {
        "timestamp": "2026-06-01T10:00:00Z",
        "drift_detected": True,
        "drifted_features": ["T1"],
        "deviations": {"T1": 20.5},
        "clean_row_count": 100,
    }
    with patch("src.api.routes.database.get_latest_drift_event", return_value=mock_event):
        response = client.get("/api/v1/monitor/drift")
    assert response.status_code == 200
    body = response.json()
    assert body["drift_detected"] is True
    assert body["drifted_features"] == ["T1"]
    assert body["deviations"]["T1"] == 20.5
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

