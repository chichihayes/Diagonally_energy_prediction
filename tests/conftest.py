from unittest.mock import MagicMock, patch

# Pre-import database.py while create_client is mocked so the module-level
# supabase client never attempts a real connection during the test suite.
with patch("supabase.create_client", return_value=MagicMock()):
    import src.services.database  # noqa: F401
