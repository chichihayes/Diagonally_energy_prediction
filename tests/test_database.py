import pytest
from unittest.mock import MagicMock, patch


@pytest.fixture
def db_chain():
    """Returns a mock that simulates Supabase's builder chain."""
    chain = MagicMock()
    chain.select.return_value = chain
    chain.order.return_value = chain
    chain.limit.return_value = chain
    chain.eq.return_value = chain
    chain.execute.return_value = MagicMock(data=[])
    return chain


@pytest.fixture
def mock_supabase(db_chain):
    client = MagicMock()
    client.table.return_value = db_chain
    with patch("src.services.database.supabase", client):
        yield db_chain


def test_get_predictions_returns_list(mock_supabase):
    from src.services.database import get_predictions

    result = get_predictions()
    assert isinstance(result, list)


def test_get_predictions_filters_by_tier(mock_supabase):
    from src.services.database import get_predictions

    mock_supabase.execute.return_value = MagicMock(
        data=[
            {
                "id": "a",
                "tier": "simple",
                "predicted_wh": 60.0,
                "predicted_kwh": 0.06,
                "estimated_cost_ngn": 4.08,
                "location": "Lagos",
                "created_at": "2026-06-01T10:00:00Z",
            }
        ]
    )

    result = get_predictions(tier="simple")

    mock_supabase.eq.assert_called_once_with("tier", "simple")
    assert all(row["tier"] == "simple" for row in result)


def test_get_predictions_respects_limit(mock_supabase):
    from src.services.database import get_predictions

    rows = [
        {
            "id": str(i),
            "tier": "full",
            "predicted_wh": 80.0,
            "predicted_kwh": 0.08,
            "estimated_cost_ngn": 5.44,
            "location": "Abuja",
            "created_at": f"2026-06-01T0{i}:00:00Z",
        }
        for i in range(5)
    ]
    mock_supabase.execute.return_value = MagicMock(data=rows[:3])

    result = get_predictions(limit=3)

    mock_supabase.limit.assert_called_once_with(3)
    assert len(result) <= 3


def test_get_predictions_default_limit_is_10(mock_supabase):
    from src.services.database import get_predictions

    get_predictions()

    mock_supabase.limit.assert_called_once_with(10)


def test_insert_prediction_calls_supabase_insert():
    from unittest.mock import MagicMock, patch
    from src.services.database import insert_prediction

    mock_client = MagicMock()
    mock_client.table.return_value.insert.return_value.execute.return_value = MagicMock()
    with patch("src.services.database.supabase", mock_client):
        insert_prediction({
            "tier": "simple",
            "predicted_wh": 60.5,
            "predicted_kwh": 0.0605,
            "estimated_cost_ngn": 4.11,
            "location": "Lagos",
            "input_features": {"lights": 0, "T1": 19.89},
        })
    mock_client.table.assert_called_once_with("predictions")
    mock_client.table.return_value.insert.assert_called_once()
