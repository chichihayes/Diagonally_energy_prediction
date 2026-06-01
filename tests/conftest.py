from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

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
