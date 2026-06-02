import json
import os
import pytest

FULL_FEATURES = [
    "lights", "T1", "RH_1", "T2", "RH_2", "T3", "RH_3", "T4", "RH_4",
    "T5", "RH_5", "T6", "RH_6", "T7", "RH_7", "T8", "RH_8", "T9", "RH_9",
    "T_out", "Press_mm_hg", "RH_out", "Windspeed", "Visibility", "Tdewpoint",
]


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
