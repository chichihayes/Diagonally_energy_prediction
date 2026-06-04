import os

from supabase import create_client, Client

supabase: Client = create_client(
    os.environ.get("SUPABASE_URL", ""),
    os.environ.get("SUPABASE_SERVICE_ROLE_KEY", os.environ.get("SUPABASE_ANON_KEY", "")),
)


def insert_forecast_request(record: dict) -> None:
    supabase.table("forecast_requests").insert(record).execute()
