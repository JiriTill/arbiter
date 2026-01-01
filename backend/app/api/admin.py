"""
Admin API endpoints for content management and analytics.
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from app.db import (
    get_feedback_repo,
    get_costs_repo,
    FeedbackRepository,
    CostsRepository,
)


router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/feedback")
async def get_feedback(
    type: str | None = None,
    limit: int = 20,
    offset: int = 0,
    feedback_repo: FeedbackRepository = Depends(get_feedback_repo),
) -> list[dict[str, Any]]:
    """
    Get recent user feedback with search/filter options.
    """
    return await feedback_repo.get_recent_feedback(
        feedback_type=type,
        limit=limit,
        offset=offset,
    )


@router.get("/costs")
async def get_costs(
    period: str = "today",
    costs_repo: CostsRepository = Depends(get_costs_repo)
):
    """
    Get API cost statistics.
    Period can be 'today', 'week', 'month'.
    """
    return await costs_repo.get_stats(period)
