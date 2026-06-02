import json
import os
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

_MOCK_TRAINING_STATS = {feat: {"mean": 20.0, "std": 1.0} for feat in [
    "lights", "T1", "RH_1", "T2", "RH_2", "T3", "RH_3", "T4", "RH_4",
    "T5", "RH_5", "T6", "RH_6", "T7", "RH_7", "T8", "RH_8", "T9", "RH_9",
    "T_out", "Press_mm_hg", "RH_out", "Windspeed", "Visibility", "Tdewpoint",
]}

# Ensure trained/ directory and training_stats.json exist before importing
# monitor.py so the module-level open() does not raise FileNotFoundError.
_STATS_PATH = os.path.join("src", "model", "trained", "training_stats.json")
os.makedirs(os.path.dirname(_STATS_PATH), exist_ok=True)
if not os.path.exists(_STATS_PATH):
    with open(_STATS_PATH, "w") as _f:
        json.dump(_MOCK_TRAINING_STATS, _f)

# Pre-import database.py while create_client is mocked so the module-level
# supabase client never attempts a real connection during the test suite.
with patch("supabase.create_client", return_value=MagicMock()):
    import src.services.database  # noqa: F401
    from src.api.main import app


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def mock_get_predictions():
    with patch("src.services.database.get_predictions") as mock:
        yield mock
