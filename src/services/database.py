import os

from supabase import create_client, Client

supabase: Client = create_client(
    os.environ.get("SUPABASE_URL", ""),
    os.environ.get("SUPABASE_ANON_KEY", ""),
)


def insert_reading(row: dict) -> None:
    supabase.table("readings").insert(row).execute()


def get_readings(limit: int = 10, since: str | None = None) -> list[dict]:
    query = supabase.table("readings").select("*").order("timestamp", desc=True)
    if since is not None:
        query = query.gte("timestamp", since)
    return query.limit(limit).execute().data


def store_anomaly(record: dict) -> None:
    supabase.table("anomalies").insert(record).execute()


def insert_forecast(row: dict) -> None:
    supabase.table("forecast").insert(row).execute()
