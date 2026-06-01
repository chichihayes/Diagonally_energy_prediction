import pytest
from unittest.mock import patch
import pandas as pd
from datetime import date, timedelta


def _make_mock_prophet_output() -> pd.DataFrame:
    today = date.today()
    rows = []
    for i in range(7):
        rows.append({
            "ds": pd.Timestamp(today + timedelta(days=i)),
            "yhat": 6000.0 + i * 100,
            "yhat_lower": 4000.0 + i * 100,
            "yhat_upper": 8000.0 + i * 100,
        })
    return pd.DataFrame(rows)


def test_forecast_7d_returns_7_element_list():
    from src.model.forecast import forecast_7d
    mock_df = _make_mock_prophet_output()
    with patch("src.model.forecast._model") as mock_model, \
         patch.dict("os.environ", {"ELECTRICITY_TARIFF_NGN_PER_KWH": "68.00"}):
        mock_model.predict.return_value = mock_df
        result = forecast_7d()
    assert len(result["forecast"]) == 7


def test_forecast_7d_each_row_has_required_keys():
    from src.model.forecast import forecast_7d
    mock_df = _make_mock_prophet_output()
    with patch("src.model.forecast._model") as mock_model, \
         patch.dict("os.environ", {"ELECTRICITY_TARIFF_NGN_PER_KWH": "68.00"}):
        mock_model.predict.return_value = mock_df
        result = forecast_7d()
    required = {"date", "predicted_wh", "predicted_kwh", "lower_wh", "upper_wh", "estimated_cost_ngn"}
    for row in result["forecast"]:
        assert required.issubset(row.keys())


def test_forecast_7d_predicted_kwh_equals_wh_over_1000():
    from src.model.forecast import forecast_7d
    mock_df = _make_mock_prophet_output()
    with patch("src.model.forecast._model") as mock_model, \
         patch.dict("os.environ", {"ELECTRICITY_TARIFF_NGN_PER_KWH": "68.00"}):
        mock_model.predict.return_value = mock_df
        result = forecast_7d()
    for row in result["forecast"]:
        assert row["predicted_kwh"] == pytest.approx(row["predicted_wh"] / 1000, rel=1e-5)


def test_forecast_7d_peak_and_lowest_day_correct():
    from src.model.forecast import forecast_7d
    mock_df = _make_mock_prophet_output()
    # Row 6 has highest yhat (6600.0), row 0 has lowest yhat (6000.0)
    with patch("src.model.forecast._model") as mock_model, \
         patch.dict("os.environ", {"ELECTRICITY_TARIFF_NGN_PER_KWH": "68.00"}):
        mock_model.predict.return_value = mock_df
        result = forecast_7d()
    today = date.today()
    assert result["peak_day"] == (today + timedelta(days=6)).strftime("%A")
    assert result["lowest_day"] == today.strftime("%A")
