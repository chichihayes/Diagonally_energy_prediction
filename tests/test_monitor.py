import json
import os
import pytest
from unittest.mock import patch

from src.services.data_loader import MODEL_FEATURES


MOCK_STATS = {
    "lag_1": {"mean": 500.0, "std": 100.0},
    "hour": {"mean": 11.5, "std": 6.9},
    "rolling_mean_6": {"mean": 450.0, "std": 80.0},
}


def test_check_anomaly_flags_extreme_value():
    from src.services import monitor
    with patch.object(monitor, "_training_stats", MOCK_STATS):
        result = monitor.check_anomaly({"lag_1": 3000.0, "hour": 11.5, "rolling_mean_6": 450.0})
    assert result["is_anomaly"] is True
    assert "lag_1" in result["flagged_features"]
    assert result["z_scores"]["lag_1"] == pytest.approx(25.0, abs=0.1)


def test_check_anomaly_normal_values_return_false():
    from src.services import monitor
    with patch.object(monitor, "_training_stats", MOCK_STATS):
        result = monitor.check_anomaly({"lag_1": 510.0, "hour": 12.0, "rolling_mean_6": 460.0})
    assert result["is_anomaly"] is False
    assert result["flagged_features"] == []


def test_check_anomaly_skips_zero_std_feature():
    stats = {"lag_1": {"mean": 500.0, "std": 0.0}, "hour": {"mean": 11.5, "std": 6.9}}
    from src.services import monitor
    with patch.object(monitor, "_training_stats", stats):
        result = monitor.check_anomaly({"lag_1": 9999.0, "hour": 11.5})
    assert "lag_1" not in result["z_scores"]
    assert "lag_1" not in result["flagged_features"]


def test_check_anomaly_result_has_required_keys():
    from src.services import monitor
    with patch.object(monitor, "_training_stats", MOCK_STATS):
        result = monitor.check_anomaly({"lag_1": 500.0, "hour": 11.5, "rolling_mean_6": 450.0})
    assert set(result.keys()) == {"is_anomaly", "z_scores", "flagged_features"}


def test_check_anomaly_ignores_unknown_features():
    from src.services import monitor
    with patch.object(monitor, "_training_stats", MOCK_STATS):
        result = monitor.check_anomaly({"lag_1": 500.0, "unknown_col": 999.0})
    assert "unknown_col" not in result["z_scores"]
    assert result["is_anomaly"] is False


def test_training_stats_json_has_correct_structure():
    stats_path = "src/model/trained/training_stats.json"
    if not os.path.exists(stats_path):
        pytest.skip("training_stats.json not yet generated — run load_and_split() first")
    with open(stats_path) as f:
        stats = json.load(f)
    assert set(stats.keys()) == set(MODEL_FEATURES)
    for feat in MODEL_FEATURES:
        assert "mean" in stats[feat], f"missing 'mean' for {feat}"
        assert "std" in stats[feat], f"missing 'std' for {feat}"
        assert isinstance(stats[feat]["mean"], float), f"mean for {feat} is not float"
        assert isinstance(stats[feat]["std"], float), f"std for {feat} is not float"
