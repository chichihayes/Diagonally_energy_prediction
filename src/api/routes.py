from typing import Optional

from fastapi import APIRouter, Query

from src.services.database import get_predictions

router = APIRouter()


@router.get("/predictions")
def list_predictions(
    tier: Optional[str] = Query(default=None),
    limit: int = Query(default=20),
):
    return get_predictions(tier=tier, limit=limit)
