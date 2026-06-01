import pytest
from unittest.mock import MagicMock


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
    mock_get_predictions.assert_called_once_with(tier="simple", limit=20)


def test_get_predictions_limit_param(client, mock_get_predictions):
    mock_get_predictions.return_value = []
    response = client.get("/api/v1/predictions?limit=5")
    assert response.status_code == 200
    mock_get_predictions.assert_called_once_with(tier=None, limit=5)


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
