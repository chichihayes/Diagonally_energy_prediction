import json
import os
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

_APPLIANCE_COLS = [
    "Fridge", "ChestFreezer", "UprightFreezer", "TumbleDryer",
    "WashingMachine", "Dishwasher", "Computer", "Television",
    "ElectricHeater", "aggregate_wh",
]

_MOCK_TRAINING_STATS = {
    "appliance_stats": {col: {"mean": 100.0, "std": 20.0} for col in _APPLIANCE_COLS},
    "overnight_thresholds": {
        "TumbleDryer": 50.0, "WashingMachine": 100.0, "Dishwasher": 60.0,
        "Computer": 30.0, "Television": 40.0, "ElectricHeater": 100.0,
    },
}

_STATS_PATH = os.path.join("src", "model", "trained", "training_stats.json")
os.makedirs(os.path.dirname(_STATS_PATH), exist_ok=True)
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
def mock_get_readings():
    with patch("src.services.database.get_readings") as mock:
        yield mock
