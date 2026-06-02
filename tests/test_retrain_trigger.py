import pytest
from src.services.retrain_trigger import should_retrain


def test_should_retrain_all_conditions_true_returns_true():
    # 2000 / 2200 = 0.909 — passes 90% threshold
    assert should_retrain(True, 2000, 2200) is True


def test_should_retrain_drift_false_returns_false():
    assert should_retrain(False, 2000, 2200) is False


def test_should_retrain_clean_count_below_threshold_returns_false():
    # 1999 < 2000 — fails C2
    assert should_retrain(True, 1999, 1999) is False


def test_should_retrain_anomaly_rate_too_high_returns_false():
    # 2000 / 3000 = 0.667 — fails C3
    assert should_retrain(True, 2000, 3000) is False


def test_should_retrain_c1_c2_both_false_returns_false():
    assert should_retrain(False, 1999, 1999) is False


def test_should_retrain_c1_c3_both_false_returns_false():
    assert should_retrain(False, 2000, 3000) is False


def test_should_retrain_c2_c3_both_false_returns_false():
    # 1000 / 3000 = 0.333 — fails C2 and C3
    assert should_retrain(True, 1000, 3000) is False


def test_should_retrain_all_conditions_false_returns_false():
    assert should_retrain(False, 1000, 3000) is False
