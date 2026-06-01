import os

from supabase import create_client, Client

supabase: Client = create_client(
    os.getenv("SUPABASE_URL", ""),
    os.getenv("SUPABASE_ANON_KEY", ""),
)


def insert_prediction(row: dict) -> None:
    supabase.table("predictions").insert(row).execute()


def get_predictions(tier: str | None = None, limit: int = 10) -> list[dict]:
    query = (
        supabase.table("predictions")
        .select("id, tier, predicted_wh, predicted_kwh, estimated_cost_ngn, location, created_at, input_features")
        .order("created_at", desc=True)
        .limit(limit)
    )
    if tier is not None:
        query = query.eq("tier", tier)
    response = query.execute()
    return response.data
