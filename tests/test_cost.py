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


def test_project_weekly_bill_returns_correct_keys():
    from src.services.cost import project_weekly_bill
    with patch.dict("os.environ", {"ELECTRICITY_TARIFF_GBP_PER_KWH": "0.34"}):
        result = project_weekly_bill(_MOCK_FORECAST)
    assert set(result.keys()) == {"optimistic_gbp", "most_likely_gbp", "pessimistic_gbp", "period"}


def test_project_weekly_bill_period_is_7_days():
    from src.services.cost import project_weekly_bill
    with patch.dict("os.environ", {"ELECTRICITY_TARIFF_GBP_PER_KWH": "0.34"}):
        result = project_weekly_bill(_MOCK_FORECAST)
    assert result["period"] == "7 days"


def test_project_weekly_bill_optimistic_gbp_correct():
    from src.services.cost import project_weekly_bill
    with patch.dict("os.environ", {"ELECTRICITY_TARIFF_GBP_PER_KWH": "0.34"}):
        result = project_weekly_bill(_MOCK_FORECAST)
    expected = round(sum(r["lower_wh"] for r in _MOCK_FORECAST) / 1000 * 0.34, 2)
    assert result["optimistic_gbp"] == pytest.approx(expected, abs=0.01)


def test_project_weekly_bill_most_likely_gbp_correct():
    from src.services.cost import project_weekly_bill
    with patch.dict("os.environ", {"ELECTRICITY_TARIFF_GBP_PER_KWH": "0.34"}):
        result = project_weekly_bill(_MOCK_FORECAST)
    expected = round(sum(r["predicted_wh"] for r in _MOCK_FORECAST) / 1000 * 0.34, 2)
    assert result["most_likely_gbp"] == pytest.approx(expected, abs=0.01)


def test_project_weekly_bill_pessimistic_gbp_correct_and_ordering():
    from src.services.cost import project_weekly_bill
    with patch.dict("os.environ", {"ELECTRICITY_TARIFF_GBP_PER_KWH": "0.34"}):
        result = project_weekly_bill(_MOCK_FORECAST)
    expected = round(sum(r["upper_wh"] for r in _MOCK_FORECAST) / 1000 * 0.34, 2)
    assert result["pessimistic_gbp"] == pytest.approx(expected, abs=0.01)
    assert result["optimistic_gbp"] <= result["most_likely_gbp"] <= result["pessimistic_gbp"]


def test_wh_to_cost_converts_correctly(monkeypatch):
    monkeypatch.setenv("ELECTRICITY_TARIFF_GBP_PER_KWH", "0.34")
    from src.services.cost import wh_to_cost
    kwh, cost = wh_to_cost(1000.0)
    assert kwh == pytest.approx(1.0)
    assert cost == pytest.approx(0.34)


def test_wh_to_cost_rounds_to_2dp(monkeypatch):
    monkeypatch.setenv("ELECTRICITY_TARIFF_GBP_PER_KWH", "0.34")
    from src.services.cost import wh_to_cost
    _, cost = wh_to_cost(60.5)
    assert cost == round(0.0605 * 0.34, 2)


def test_wh_to_cost_reads_tariff_from_env(monkeypatch):
    monkeypatch.setenv("ELECTRICITY_TARIFF_GBP_PER_KWH", "0.50")
    from src.services import cost as cost_module
    importlib.reload(cost_module)
    _, gbp = cost_module.wh_to_cost(1000.0)
    assert gbp == pytest.approx(0.50)


_COST_MOCK_FORECAST = [
    {"predicted_wh": 6000.0, "lower_wh": 4000.0, "upper_wh": 8000.0},
] * 7
# sum(lower_wh)  = 28000 Wh = 28 kWh  → 28 * 0.34 = 9.52
# sum(predicted) = 42000 Wh = 42 kWh  → 42 * 0.34 = 14.28
# sum(upper_wh)  = 56000 Wh = 56 kWh  → 56 * 0.34 = 19.04


def test_project_weekly_bill_optimistic_uses_lower_wh():
    from src.services.cost import project_weekly_bill
    with patch.dict("os.environ", {"ELECTRICITY_TARIFF_GBP_PER_KWH": "0.34"}):
        result = project_weekly_bill(_COST_MOCK_FORECAST)
    assert result["optimistic_gbp"] == pytest.approx(9.52, abs=0.01)


def test_project_weekly_bill_most_likely_uses_predicted_wh():
    from src.services.cost import project_weekly_bill
    with patch.dict("os.environ", {"ELECTRICITY_TARIFF_GBP_PER_KWH": "0.34"}):
        result = project_weekly_bill(_COST_MOCK_FORECAST)
    assert result["most_likely_gbp"] == pytest.approx(14.28, abs=0.01)


def test_project_weekly_bill_pessimistic_uses_upper_wh():
    from src.services.cost import project_weekly_bill
    with patch.dict("os.environ", {"ELECTRICITY_TARIFF_GBP_PER_KWH": "0.34"}):
        result = project_weekly_bill(_COST_MOCK_FORECAST)
    assert result["pessimistic_gbp"] == pytest.approx(19.04, abs=0.01)
