import os

from supabase import create_client, Client

supabase: Client = create_client(
    os.environ.get("SUPABASE_URL", ""),
    os.environ.get("SUPABASE_ANON_KEY", ""),
)


def insert_prediction(row: dict) -> None:
    supabase.table("predictions").insert(row).execute()


def fetch_clean_rows() -> list[dict]:
    return supabase.table("predictions").select("*").execute().data


def get_predictions(tier: str | None = None, limit: int = 10, since: str | None = None) -> list[dict]:
    query = supabase.table("predictions").select("*").order("created_at", desc=True)
    if since is not None:
        query = query.gte("created_at", since)
    if tier is not None:
        query = query.eq("tier", tier)
    return query.limit(limit).execute().data


def store_drift_event(record: dict) -> None:
    supabase.table("drift_log").insert(record).execute()


def get_latest_drift_event() -> dict | None:
    result = supabase.table("drift_log").select("*").order("timestamp", desc=True).limit(1).execute()
    return result.data[0] if result.data else None


def store_anomaly(record: dict) -> None:
    supabase.table("anomalies").insert(record).execute()


def get_last_n_clean_readings(n: int) -> list[dict]:
    result = (
        supabase.table("predictions")
        .select("input_features")
        .eq("low_confidence", False)
        .order("created_at", desc=True)
        .limit(n)
        .execute()
    )
    return [row["input_features"] for row in result.data]


def insert_forecast(row: dict) -> None:
    supabase.table("forecast").insert(row).execute()
