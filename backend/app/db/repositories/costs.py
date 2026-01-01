from datetime import datetime
from app.db.repositories.base import BaseRepository
from app.db.models import ApiCost, ApiCostCreate

class CostsRepository(BaseRepository[ApiCost, ApiCostCreate]):
    def __init__(self, conn):
        super().__init__(conn)
        
    async def log_cost(self, cost: ApiCostCreate) -> ApiCost:
        query = """
            INSERT INTO api_costs (
                request_id, endpoint, model, input_tokens, output_tokens, 
                cost_usd, cache_hit
            )
            VALUES (
                %(request_id)s, %(endpoint)s, %(model)s, %(input_tokens)s, 
                %(output_tokens)s, %(cost_usd)s, %(cache_hit)s
            )
            RETURNING id, created_at
        """
        async with self._get_cursor() as cur:
            await cur.execute(query, cost.model_dump())
            row = await cur.fetchone()
            
            return ApiCost(
                id=row["id"],
                created_at=row["created_at"],
                **cost.model_dump()
            )

    async def get_daily_spend(self) -> float:
        """Calculate total spend in the last 24 hours."""
        query = """
            SELECT SUM(cost_usd) as total
            FROM api_costs
            WHERE created_at > NOW() - INTERVAL '24 hours'
        """
        async with self._get_cursor() as cur:
            await cur.execute(query)
            row = await cur.fetchone()
            return float(row["total"] or 0.0)

    async def get_stats(self, period: str = "today") -> dict:
        """Get cost statistics (total, count, avg) for a period."""
        # period: today, week, month
        interval = "24 hours"
        if period == "week":
            interval = "7 days"
        elif period == "month":
            interval = "30 days"
            
        where_clause = f"created_at > NOW() - INTERVAL '{interval}'"
        
        # Summary
        query_summary = f"""
            SELECT 
                COALESCE(SUM(cost_usd), 0) as total_cost,
                COUNT(*) as total_requests,
                AVG(cost_usd) as avg_cost
            FROM api_costs
            WHERE {where_clause}
        """
        
        # Breakdown by endpoint/model
        query_breakdown = f"""
            SELECT 
                endpoint, 
                model, 
                COUNT(*) as count,
                SUM(cost_usd) as cost
            FROM api_costs
            WHERE {where_clause}
            GROUP BY endpoint, model
            ORDER BY cost DESC
        """
        
        async with self._get_cursor() as cur:
            await cur.execute(query_summary)
            summary = await cur.fetchone()
            
            await cur.execute(query_breakdown)
            breakdown = await cur.fetchall()
            
            return {
                "total_cost": float(summary["total_cost"]),
                "total_requests": summary["total_requests"],
                "avg_cost": float(summary["avg_cost"] or 0.0),
                "breakdown": [dict(row) for row in breakdown]
            }
