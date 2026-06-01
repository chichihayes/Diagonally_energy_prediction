import os

from supabase import create_client, Client

_client: Client | None = None


def _get_client() -> Client:
    global _client
    if _client is None:
        _client = create_client(
            os.environ["SUPABASE_URL"],
            os.environ["SUPABASE_ANON_KEY"],
        )
    return _client


def get_predictions(tier: str | None = None, limit: int = 10) -> list[dict]:
    query = (
        _get_client().table("predictions")
        .select("id, tier, predicted_wh, predicted_kwh, estimated_cost_ngn, location, created_at, input_features")
        .order("created_at", desc=True)
        .limit(limit)
    )
    if tier is not None:
        query = query.eq("tier", tier)
    response = query.execute()
    return response.data
