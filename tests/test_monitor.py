import pytest
from unittest.mock import patch

import src.services.monitor as monitor_mod

_APPLIANCE_STATS = {
    "Fridge":         {"mean": 74.2,  "std": 15.3},
    "ChestFreezer":   {"mean": 80.1,  "std": 12.4},
    "UprightFreezer": {"mean": 65.8,  "std": 10.2},
    "TumbleDryer":    {"mean": 12.4,  "std": 45.6},
    "WashingMachine": {"mean": 18.9,  "std": 78.3},
    "Dishwasher":     {"mean": 8.2,   "std": 32.1},
    "Computer":       {"mean": 45.6,  "std": 28.9},
    "Television":     {"mean": 38.7,  "std": 42.1},
    "ElectricHeater": {"mean": 95.4,  "std": 210.6},
    "aggregate_wh":   {"mean": 523.1, "std": 312.4},
}

_MOCK_STATS = {"appliance_stats": _APPLIANCE_STATS}


def test_normal_readings_no_anomaly():
    values = {k: v["mean"] for k, v in _APPLIANCE_STATS.items()}
    with patch.object(monitor_mod, "_stats", _MOCK_STATS):
        result = monitor_mod.check_anomaly(values)
    assert result["is_anomaly"] is False
    assert result["flagged_appliances"] == []


def test_fridge_low_anomaly():
    # z = (5 - 74.2) / 15.3 ≈ -4.52 → LOW
    values = {k: v["mean"] for k, v in _APPLIANCE_STATS.items()}
    values["Fridge"] = 5.0
    with patch.object(monitor_mod, "_stats", _MOCK_STATS):
        result = monitor_mod.check_anomaly(values)
    assert result["is_anomaly"] is True
    fridge_flag = next(f for f in result["flagged_appliances"] if f["appliance"] == "Fridge")
    assert fridge_flag["direction"] == "LOW"


def test_electric_heater_high_anomaly():
    # z = (5000 - 95.4) / 210.6 ≈ 23.3 → HIGH
    values = {k: v["mean"] for k, v in _APPLIANCE_STATS.items()}
    values["ElectricHeater"] = 5000.0
    with patch.object(monitor_mod, "_stats", _MOCK_STATS):
        result = monitor_mod.check_anomaly(values)
    assert result["is_anomaly"] is True
    heater_flag = next(f for f in result["flagged_appliances"] if f["appliance"] == "ElectricHeater")
    assert heater_flag["direction"] == "HIGH"


def test_multiple_appliances_flagged_simultaneously():
    values = {k: v["mean"] for k, v in _APPLIANCE_STATS.items()}
    values["Fridge"] = 5.0          # LOW
    values["ElectricHeater"] = 5000.0  # HIGH
    with patch.object(monitor_mod, "_stats", _MOCK_STATS):
        result = monitor_mod.check_anomaly(values)
    assert result["is_anomaly"] is True
    names = [f["appliance"] for f in result["flagged_appliances"]]
    assert "Fridge" in names
    assert "ElectricHeater" in names


def test_zero_std_feature_skipped():
    stats = {"appliance_stats": {"Fridge": {"mean": 74.2, "std": 0.0}}}
    with patch.object(monitor_mod, "_stats", stats):
        result = monitor_mod.check_anomaly({"Fridge": 9999.0})
    assert "Fridge" not in result["z_scores"]
    assert result["is_anomaly"] is False


def test_missing_stats_file_raises_file_not_found(tmp_path, monkeypatch):
    monkeypatch.setattr(monitor_mod, "_STATS_PATH", str(tmp_path / "missing.json"))
    monkeypatch.setattr(monitor_mod, "_stats", None)
    with pytest.raises(FileNotFoundError):
        monitor_mod.check_anomaly({"Fridge": 74.2})
