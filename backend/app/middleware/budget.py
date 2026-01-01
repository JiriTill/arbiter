"""
Middleware/Dependency for enforcing daily API budget.
"""
import os
import logging
from datetime import datetime, timedelta

from fastapi import HTTPException, Depends
from app.db import get_costs_repo, CostsRepository

logger = logging.getLogger(__name__)

# Default budget: $10.00
DEFAULT_BUDGET = 10.0

async def check_budget(costs_repo: CostsRepository = Depends(get_costs_repo)):
    """
    Check if the daily API budget has been exceeded.
    Raises 503 Service Unavailable if exceeded.
    """
    # Get budget from env
    try:
        daily_budget = float(os.getenv("DAILY_BUDGET_USD", str(DEFAULT_BUDGET)))
    except ValueError:
        daily_budget = DEFAULT_BUDGET
        logger.warning(f"Invalid DAILY_BUDGET_USD value, using default: {DEFAULT_BUDGET}")
    
    # Get current spend
    current_spend = await costs_repo.get_daily_spend()
    
    if current_spend >= daily_budget:
        logger.warning(f"Daily budget exceeded: ${current_spend:.2f} / ${daily_budget:.2f}")
        
        # Calculate approximate reset time (tomorrow midnight UTC)
        next_day = (datetime.utcnow() + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        retry_after = next_day.isoformat() + "Z"
        
        raise HTTPException(
            status_code=503,
            detail={
                "error": "Daily budget limit reached",
                "message": "We've reached our daily API budget. Please try again tomorrow.",
                "retry_after": retry_after
            }
        )
