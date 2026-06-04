from unittest.mock import MagicMock, patch


def test_insert_forecast_request_calls_supabase_insert():
    from src.services.database import insert_forecast_request
    mock_client = MagicMock()
    mock_client.table.return_value.insert.return_value.execute.return_value = MagicMock()
    with patch("src.services.database.supabase", mock_client):
        insert_forecast_request({
            "input_date": "2024-03-15",
            "lag_1": 7200.0,
            "predicted_wh": 7400.0,
            "estimated_cost_gbp": 2.52,
        })
    mock_client.table.assert_called_once_with("forecast_requests")
    mock_client.table.return_value.insert.assert_called_once()
