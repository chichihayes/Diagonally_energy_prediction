import json
import os
import pytest
from unittest.mock import patch

FULL_FEATURES = [
    "lights", "T1", "RH_1", "T2", "RH_2", "T3", "RH_3", "T4", "RH_4",
    "T5", "RH_5", "T6", "RH_6", "T7", "RH_7", "T8", "RH_8", "T9", "RH_9",
    "T_out", "Press_mm_hg", "RH_out", "Windspeed", "Visibility", "Tdewpoint",
]


MOCK_STATS = {
    "T1": {"mean": 20.0, "std": 1.0},
    "lights": {"mean": 50.0, "std": 10.0},
    "RH_1": {"mean": 45.0, "std": 5.0},
}


def test_check_anomaly_flags_extreme_value():
    from src.services import monitor
    with patch.object(monitor, "_training_stats", MOCK_STATS):
        result = monitor.check_anomaly({"T1": 50.0, "lights": 50.0, "RH_1": 45.0})
    assert result["is_anomaly"] is True
    assert "T1" in result["flagged_features"]
    assert result["z_scores"]["T1"] == pytest.approx(30.0, abs=0.1)


def test_check_anomaly_normal_values_return_false():
    from src.services import monitor
    with patch.object(monitor, "_training_stats", MOCK_STATS):
        result = monitor.check_anomaly({"T1": 20.5, "lights": 52.0, "RH_1": 44.0})
    assert result["is_anomaly"] is False
    assert result["flagged_features"] == []


def test_check_anomaly_skips_zero_std_feature():
    stats = {"T1": {"mean": 20.0, "std": 0.0}, "lights": {"mean": 50.0, "std": 10.0}}
    from src.services import monitor
    with patch.object(monitor, "_training_stats", stats):
        result = monitor.check_anomaly({"T1": 9999.0, "lights": 50.0})
    assert "T1" not in result["z_scores"]
    assert "T1" not in result["flagged_features"]


def test_check_anomaly_result_has_required_keys():
    from src.services import monitor
    with patch.object(monitor, "_training_stats", MOCK_STATS):
        result = monitor.check_anomaly({"T1": 20.0, "lights": 50.0, "RH_1": 45.0})
    assert set(result.keys()) == {"is_anomaly", "z_scores", "flagged_features"}


def test_check_anomaly_ignores_unknown_features():
    from src.services import monitor
    with patch.object(monitor, "_training_stats", MOCK_STATS):
        result = monitor.check_anomaly({"T1": 20.0, "unknown_col": 999.0})
    assert "unknown_col" not in result["z_scores"]
    assert result["is_anomaly"] is False


def test_training_stats_json_has_correct_structure():
    stats_path = "src/model/trained/training_stats.json"
    if not os.path.exists(stats_path):
        pytest.skip("training_stats.json not yet generated — run scripts/run_training_full.py first")
    with open(stats_path) as f:
        stats = json.load(f)
    assert set(stats.keys()) == set(FULL_FEATURES)
    for feat in FULL_FEATURES:
        assert "mean" in stats[feat], f"missing 'mean' for {feat}"
        assert "std" in stats[feat], f"missing 'std' for {feat}"
        assert isinstance(stats[feat]["mean"], float), f"mean for {feat} is not float"
        assert isinstance(stats[feat]["std"], float), f"std for {feat} is not float"
