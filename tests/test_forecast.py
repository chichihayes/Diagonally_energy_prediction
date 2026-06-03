import os
import importlib

import joblib
import pytest
from unittest.mock import patch, MagicMock
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


def _make_mock_artifact(yhat=200.0):
    mock_model = MagicMock()
    mock_model.predict.return_value = pd.DataFrame({
        "ds": pd.date_range("2013-12-16", periods=24, freq="h"),
        "yhat": [yhat] * 24,
        "yhat_lower": [yhat * 0.85] * 24,
        "yhat_upper": [yhat * 1.15] * 24,
    })
    return {"model": mock_model, "model_type": "Prophet"}


def test_forecast_7d_returns_7_element_list():
    from src.model.forecast import forecast_7d
    mock_df = _make_mock_prophet_output()
    with patch("src.model.forecast._model") as mock_model, \
         patch.dict("os.environ", {"ELECTRICITY_TARIFF_GBP_PER_KWH": "0.34"}):
        mock_model.predict.return_value = mock_df
        result = forecast_7d()
    assert len(result["forecast"]) == 7


def test_forecast_7d_each_row_has_required_keys():
    from src.model.forecast import forecast_7d
    mock_df = _make_mock_prophet_output()
    with patch("src.model.forecast._model") as mock_model, \
         patch.dict("os.environ", {"ELECTRICITY_TARIFF_GBP_PER_KWH": "0.34"}):
        mock_model.predict.return_value = mock_df
        result = forecast_7d()
    required = {"date", "predicted_wh", "predicted_kwh", "lower_wh", "upper_wh", "estimated_cost_gbp"}
    for row in result["forecast"]:
        assert required.issubset(row.keys())


def test_forecast_7d_predicted_kwh_equals_wh_over_1000():
    from src.model.forecast import forecast_7d
    mock_df = _make_mock_prophet_output()
    with patch("src.model.forecast._model") as mock_model, \
         patch.dict("os.environ", {"ELECTRICITY_TARIFF_GBP_PER_KWH": "0.34"}):
        mock_model.predict.return_value = mock_df
        result = forecast_7d()
    for row in result["forecast"]:
        assert row["predicted_kwh"] == pytest.approx(row["predicted_wh"] / 1000, rel=1e-5)


def test_forecast_7d_includes_projected_week_bill():
    from src.model.forecast import forecast_7d
    mock_df = _make_mock_prophet_output()
    with patch("src.model.forecast._model") as mock_model, \
         patch.dict("os.environ", {"ELECTRICITY_TARIFF_GBP_PER_KWH": "0.34"}):
        mock_model.predict.return_value = mock_df
        result = forecast_7d()
    bill = result["projected_week_bill"]
    assert set(bill.keys()) == {"optimistic_gbp", "most_likely_gbp", "pessimistic_gbp", "period"}
    assert bill["period"] == "7 days"
    assert bill["optimistic_gbp"] <= bill["most_likely_gbp"] <= bill["pessimistic_gbp"]


def test_forecast_7d_peak_and_lowest_day_correct():
    from src.model.forecast import forecast_7d
    mock_df = _make_mock_prophet_output()
    # Row 6 has highest yhat (6600.0), row 0 has lowest yhat (6000.0)
    with patch("src.model.forecast._model") as mock_model, \
         patch.dict("os.environ", {"ELECTRICITY_TARIFF_GBP_PER_KWH": "0.34"}):
        mock_model.predict.return_value = mock_df
        result = forecast_7d()
    today = date.today()
    assert result["peak_day"] == (today + timedelta(days=6)).strftime("%A")
    assert result["lowest_day"] == today.strftime("%A")


# ---------------------------------------------------------------------------
# forecast_24h tests
# ---------------------------------------------------------------------------

def test_forecast_model_singleton_is_same_object(monkeypatch, tmp_path):
    stub = {"model": object(), "model_type": "Prophet"}
    p = tmp_path / "model_forecast.joblib"
    joblib.dump(stub, str(p))
    monkeypatch.setenv("MODEL_PATH_FORECAST", str(p))
    import src.model.forecast as f_mod
    importlib.reload(f_mod)
    assert f_mod._artifact is f_mod._artifact


def test_forecast_24h_returns_24_elements(monkeypatch):
    import src.model.forecast as f_mod
    monkeypatch.setattr(f_mod, "_artifact", _make_mock_artifact())
    monkeypatch.setenv("ELECTRICITY_TARIFF_GBP_PER_KWH", "0.34")
    result = f_mod.forecast_24h()
    assert len(result) == 24


def test_forecast_24h_each_dict_has_required_keys(monkeypatch):
    import src.model.forecast as f_mod
    monkeypatch.setattr(f_mod, "_artifact", _make_mock_artifact())
    monkeypatch.setenv("ELECTRICITY_TARIFF_GBP_PER_KWH", "0.34")
    result = f_mod.forecast_24h()
    required = {"ds", "yhat", "yhat_lower", "yhat_upper", "predicted_kwh", "estimated_cost_gbp"}
    for item in result:
        assert set(item.keys()) == required


def test_forecast_24h_cost_calculation(monkeypatch):
    import src.model.forecast as f_mod
    monkeypatch.setattr(f_mod, "_artifact", _make_mock_artifact(yhat=1000.0))
    monkeypatch.setenv("ELECTRICITY_TARIFF_GBP_PER_KWH", "0.34")
    result = f_mod.forecast_24h()
    assert result[0]["predicted_kwh"] == 1.0
    assert result[0]["estimated_cost_gbp"] == pytest.approx(0.34)


def test_forecast_24h_lower_lte_yhat_lte_upper(monkeypatch):
    import src.model.forecast as f_mod
    monkeypatch.setattr(f_mod, "_artifact", _make_mock_artifact(yhat=300.0))
    monkeypatch.setenv("ELECTRICITY_TARIFF_GBP_PER_KWH", "0.34")
    result = f_mod.forecast_24h()
    for item in result:
        assert item["yhat_lower"] <= item["yhat"] <= item["yhat_upper"]


def test_forecast_24h_propagates_model_exception(monkeypatch):
    import src.model.forecast as f_mod
    mock_model = MagicMock()
    mock_model.predict.side_effect = RuntimeError("model crashed")
    monkeypatch.setattr(f_mod, "_artifact", {"model": mock_model, "model_type": "Prophet"})
    monkeypatch.setenv("ELECTRICITY_TARIFF_GBP_PER_KWH", "0.34")
    with pytest.raises(RuntimeError, match="model crashed"):
        f_mod.forecast_24h()
