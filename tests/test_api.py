import pytest
from unittest.mock import MagicMock


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


@pytest.fixture
def client():
    from src.api.main import app
    from fastapi.testclient import TestClient
    return TestClient(app)


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
