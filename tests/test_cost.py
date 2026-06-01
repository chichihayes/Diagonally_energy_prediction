import importlib
import pytest


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
