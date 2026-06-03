import json
import os
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from src.services.data_loader import MODEL_FEATURES

_MOCK_TRAINING_STATS = {feat: {"mean": 5.0, "std": 2.0} for feat in MODEL_FEATURES}

# Ensure trained/ directory and training_stats.json exist before importing
# monitor.py and retrain_trigger.py so their module-level open() does not raise.
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
def mock_get_predictions():
    with patch("src.services.database.get_predictions") as mock:
        yield mock
