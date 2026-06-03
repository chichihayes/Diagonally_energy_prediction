import pytest
from unittest.mock import MagicMock, patch


@pytest.fixture
def db_chain():
    chain = MagicMock()
    chain.select.return_value = chain
    chain.order.return_value = chain
    chain.limit.return_value = chain
    chain.eq.return_value = chain
    chain.gte.return_value = chain
    chain.execute.return_value = MagicMock(data=[])
    return chain


@pytest.fixture
def mock_supabase(db_chain):
    client = MagicMock()
    client.table.return_value = db_chain
    with patch("src.services.database.supabase", client):
        yield db_chain


def test_get_readings_returns_list(mock_supabase):
    from src.services.database import get_readings
    result = get_readings()
    assert isinstance(result, list)


def test_get_readings_respects_limit(mock_supabase):
    from src.services.database import get_readings
    get_readings(limit=5)
    mock_supabase.limit.assert_called_once_with(5)


def test_get_readings_default_limit_is_10(mock_supabase):
    from src.services.database import get_readings
    get_readings()
    mock_supabase.limit.assert_called_once_with(10)


def test_get_readings_since_applies_gte(mock_supabase):
    from src.services.database import get_readings
    get_readings(since="2013-12-16T10:00:00Z")
    mock_supabase.gte.assert_called_once_with("timestamp", "2013-12-16T10:00:00Z")


def test_get_readings_no_gte_when_since_is_none(mock_supabase):
    from src.services.database import get_readings
    get_readings(since=None)
    mock_supabase.gte.assert_not_called()


def test_insert_reading_calls_supabase_insert():
    from src.services.database import insert_reading
    mock_client = MagicMock()
    mock_client.table.return_value.insert.return_value.execute.return_value = MagicMock()
    with patch("src.services.database.supabase", mock_client):
        insert_reading({
            "timestamp": "2013-12-16T10:00:00",
            "aggregate_wh": 523.1,
            "fridge_wh": 74.2,
            "estimated_cost_gbp": 0.18,
        })
    mock_client.table.assert_called_once_with("readings")
    mock_client.table.return_value.insert.assert_called_once()


def test_store_anomaly_calls_supabase_insert():
    from src.services.database import store_anomaly
    record = {
        "timestamp": "2013-12-16T10:00:00",
        "appliance_values": {"Fridge": 5.0},
        "z_scores": {"Fridge": -4.52},
        "flagged_appliances": [{"appliance": "Fridge", "direction": "LOW"}],
    }
    mock_client = MagicMock()
    mock_client.table.return_value.insert.return_value.execute.return_value = MagicMock()
    with patch("src.services.database.supabase", mock_client):
        store_anomaly(record)
    mock_client.table.assert_called_once_with("anomalies")
    mock_client.table.return_value.insert.assert_called_once_with(record)
