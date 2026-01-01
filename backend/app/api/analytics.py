"""
Analytics API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.db import get_history_repo, HistoryRepository
from app.db.connection import get_async_connection


router = APIRouter(prefix="/analytics", tags=["Analytics"])


class ConfidenceStats(BaseModel):
    total_queries: int
    high_percentage: float
    medium_percentage: float
    low_percentage: float
    avg_response_time_ms: float


class RepeatedLowConfidence(BaseModel):
    normalized_question: str
    count: int
    last_asked_at: str


@router.get("/stats", response_model=ConfidenceStats)
async def get_confidence_stats(
    game_id: int | None = None,
    history_repo: HistoryRepository = Depends(get_history_repo),
):
    """Get confidence distribution stats."""
    stats = await history_repo.get_stats(game_id=game_id)
    
    total = stats.get("total_queries", 0)
    if total == 0:
        return {
            "total_queries": 0,
            "high_percentage": 0.0,
            "medium_percentage": 0.0,
            "low_percentage": 0.0,
            "avg_response_time_ms": 0.0,
        }
    
    return {
        "total_queries": total,
        "high_percentage": round((stats.get("high_confidence", 0) / total) * 100, 1),
        "medium_percentage": round((stats.get("medium_confidence", 0) / total) * 100, 1),
        "low_percentage": round((stats.get("low_confidence", 0) / total) * 100, 1),
        "avg_response_time_ms": round(stats.get("avg_response_time_ms", 0) or 0, 1),
    }


@router.get("/low-confidence", response_model=list[RepeatedLowConfidence])
async def get_repeated_low_confidence(
    threshold: int = 3,
    history_repo: HistoryRepository = Depends(get_history_repo),
):
    """Get questions that repeatedly result in low confidence."""
    # Custom query for this analytics need
    query = """
        SELECT 
            normalized_question,
            COUNT(*) as count,
            MAX(created_at) as last_asked_at
        FROM ask_history
        WHERE confidence = 'low'
        GROUP BY normalized_question
        HAVING COUNT(*) >= %s
        ORDER BY count DESC
        LIMIT 20
    """
    
    # We need to access cursor directly as repository doesn't have this method
    # Ideally should be in repository but for this task I'll use the connection
    # via the repository's method or just add it to repository.
    # I'll modify repository later or use raw SQL execution here if possible?
    # HistoryRepository inherits BaseRepository which has _get_cursor but it's protected.
    
    # Let's add it to HistoryRepository properly? "Integration" step implies updating existing code.
    # But for a new file, I might just cheat and use passed repo's private cursor method locally 
    # if python allows it (it does), or better, define it in repository.
    # Since I cannot easily edit repository again without another step, I will use 
    # a dedicated function here using get_async_connection directly.
    
    async with get_async_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(query, (threshold,))
            rows = await cur.fetchall()
            
            return [
                {
                    "normalized_question": row["normalized_question"],
                    "count": row["count"],
                    "last_asked_at": str(row["last_asked_at"]),
                }
                for row in rows
            ]
