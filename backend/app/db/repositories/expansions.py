"""
Expansions repository for managing game expansions.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel

from app.db.repositories.base import BaseRepository


class Expansion(BaseModel):
    """Expansion model."""
    id: int
    game_id: int
    name: str
    code: str
    description: str | None = None
    release_date: datetime | None = None
    display_order: int = 0
    created_at: datetime | None = None
    updated_at: datetime | None = None


class ExpansionCreate(BaseModel):
    """Expansion creation model."""
    game_id: int
    name: str
    code: str
    description: str | None = None
    release_date: datetime | None = None
    display_order: int = 0


class ExpansionsRepository(BaseRepository[Expansion, ExpansionCreate]):
    """Repository for expansions table."""
    
    table_name = "expansions"
    model_class = Expansion
    
    async def get_by_game_id(self, game_id: int) -> list[Expansion]:
        """
        Get all expansions for a game.
        
        Args:
            game_id: Game ID to filter by
            
        Returns:
            List of expansions ordered by release date (newest first)
        """
        query = """
            SELECT * FROM expansions
            WHERE game_id = %s
            ORDER BY 
                COALESCE(release_date, '1900-01-01') DESC,
                display_order ASC,
                name ASC
        """
        async with self._get_cursor() as cur:
            await cur.execute(query, (game_id,))
            rows = await cur.fetchall()
            return [Expansion.model_validate(dict(row)) for row in rows]
    
    async def get_by_code(self, game_id: int, code: str) -> Expansion | None:
        """
        Get expansion by game and code.
        
        Args:
            game_id: Game ID
            code: Expansion code (e.g., 'riverfolk')
            
        Returns:
            Expansion if found, None otherwise
        """
        query = """
            SELECT * FROM expansions
            WHERE game_id = %s AND code = %s
        """
        async with self._get_cursor() as cur:
            await cur.execute(query, (game_id, code))
            row = await cur.fetchone()
            if row:
                return Expansion.model_validate(dict(row))
            return None
    
    async def create(self, expansion: ExpansionCreate) -> Expansion:
        """
        Create a new expansion.
        
        Args:
            expansion: Expansion data
            
        Returns:
            Created expansion with ID
        """
        query = """
            INSERT INTO expansions (game_id, name, code, description, release_date, display_order)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING *
        """
        async with self._get_cursor() as cur:
            await cur.execute(query, (
                expansion.game_id,
                expansion.name,
                expansion.code,
                expansion.description,
                expansion.release_date,
                expansion.display_order,
            ))
            row = await cur.fetchone()
            await self.conn.commit()
            return Expansion.model_validate(dict(row))
    
    async def get_with_source_count(self, game_id: int) -> list[dict[str, Any]]:
        """
        Get expansions with their source counts.
        
        Args:
            game_id: Game ID
            
        Returns:
            List of expansion dicts with source_count
        """
        query = """
            SELECT 
                e.*,
                COUNT(gs.id) as source_count
            FROM expansions e
            LEFT JOIN game_sources gs ON gs.expansion_id = e.id
            WHERE e.game_id = %s
            GROUP BY e.id
            ORDER BY 
                COALESCE(e.release_date, '1900-01-01') DESC,
                e.display_order ASC
        """
        async with self._get_cursor() as cur:
            await cur.execute(query, (game_id,))
            rows = await cur.fetchall()
            return [dict(row) for row in rows]


# Dependency injection
_expansions_repo: ExpansionsRepository | None = None


async def get_expansions_repo() -> ExpansionsRepository:
    """Get or create expansions repository."""
    global _expansions_repo
    
    if _expansions_repo is None:
        from app.db.connection import get_async_pool
        pool = await get_async_pool()
        _expansions_repo = ExpansionsRepository(pool)
    
    return _expansions_repo
