from fastapi import APIRouter, Query

from src.services import database

router = APIRouter(prefix="/api/v1")


@router.get("/predictions")
def get_predictions_route(
    tier: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=50),
):
    return database.get_predictions(tier=tier, limit=limit)
