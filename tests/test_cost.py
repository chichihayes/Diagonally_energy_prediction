import importlib
import pytest
from unittest.mock import patch


_MOCK_FORECAST = [
    {"predicted_wh": 6000.0, "lower_wh": 4000.0, "upper_wh": 8000.0},
    {"predicted_wh": 6100.0, "lower_wh": 4100.0, "upper_wh": 8100.0},
    {"predicted_wh": 6200.0, "lower_wh": 4200.0, "upper_wh": 8200.0},
    {"predicted_wh": 6300.0, "lower_wh": 4300.0, "upper_wh": 8300.0},
    {"predicted_wh": 6400.0, "lower_wh": 4400.0, "upper_wh": 8400.0},
    {"predicted_wh": 6500.0, "lower_wh": 4500.0, "upper_wh": 8500.0},
    {"predicted_wh": 6600.0, "lower_wh": 4600.0, "upper_wh": 8600.0},
]


def test_project_monthly_bill_returns_correct_keys():
    from src.services.cost import project_monthly_bill
    with patch.dict("os.environ", {"ELECTRICITY_TARIFF_NGN_PER_KWH": "68.00"}):
        result = project_monthly_bill(_MOCK_FORECAST)
    assert set(result.keys()) == {"optimistic_ngn", "most_likely_ngn", "pessimistic_ngn"}


def test_project_monthly_bill_optimistic_ngn_correct():
    from src.services.cost import project_monthly_bill
    with patch.dict("os.environ", {"ELECTRICITY_TARIFF_NGN_PER_KWH": "68.00"}):
        result = project_monthly_bill(_MOCK_FORECAST)
    expected = round(sum(r["lower_wh"] for r in _MOCK_FORECAST) / 1000 * (30 / 7) * 68.00, 2)
    assert result["optimistic_ngn"] == pytest.approx(expected, abs=0.01)


def test_project_monthly_bill_most_likely_ngn_correct():
    from src.services.cost import project_monthly_bill
    with patch.dict("os.environ", {"ELECTRICITY_TARIFF_NGN_PER_KWH": "68.00"}):
        result = project_monthly_bill(_MOCK_FORECAST)
    expected = round(sum(r["predicted_wh"] for r in _MOCK_FORECAST) / 1000 * (30 / 7) * 68.00, 2)
    assert result["most_likely_ngn"] == pytest.approx(expected, abs=0.01)


def test_project_monthly_bill_pessimistic_ngn_correct_and_ordering():
    from src.services.cost import project_monthly_bill
    with patch.dict("os.environ", {"ELECTRICITY_TARIFF_NGN_PER_KWH": "68.00"}):
        result = project_monthly_bill(_MOCK_FORECAST)
    expected = round(sum(r["upper_wh"] for r in _MOCK_FORECAST) / 1000 * (30 / 7) * 68.00, 2)
    assert result["pessimistic_ngn"] == pytest.approx(expected, abs=0.01)
    assert result["optimistic_ngn"] <= result["most_likely_ngn"] <= result["pessimistic_ngn"]


def test_wh_to_cost_converts_correctly(monkeypatch):
    monkeypatch.setenv("ELECTRICITY_TARIFF_NGN_PER_KWH", "68.00")
    from src.services.cost import wh_to_cost
    kwh, cost = wh_to_cost(1000.0)
    assert kwh == pytest.approx(1.0)
    assert cost == pytest.approx(68.00)


def test_wh_to_cost_rounds_to_2dp(monkeypatch):
    monkeypatch.setenv("ELECTRICITY_TARIFF_NGN_PER_KWH", "68.00")
    from src.services.cost import wh_to_cost
    _, cost = wh_to_cost(60.5)
    assert cost == round(0.0605 * 68.00, 2)


def test_wh_to_cost_reads_tariff_from_env(monkeypatch):
    monkeypatch.setenv("ELECTRICITY_TARIFF_NGN_PER_KWH", "100.00")
    from src.services import cost as cost_module
    importlib.reload(cost_module)
    _, ngn = cost_module.wh_to_cost(1000.0)
    assert ngn == pytest.approx(100.00)
