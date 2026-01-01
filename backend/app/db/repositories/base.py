"""
Base repository class with common CRUD operations.
"""

from typing import Any, Generic, TypeVar

import psycopg
from psycopg.rows import dict_row

from app.db.models import BaseDBModel


T = TypeVar("T", bound=BaseDBModel)
CreateT = TypeVar("CreateT", bound=BaseDBModel)


class BaseRepository(Generic[T, CreateT]):
    """
    Base repository with generic CRUD operations.
    
    Usage:
        class GamesRepository(BaseRepository[Game, GameCreate]):
            table_name = "games"
            model_class = Game
    """
    
    table_name: str = ""
    model_class: type[T]
    
    def __init__(self, connection: psycopg.AsyncConnection | psycopg.Connection):
        """Initialize with a database connection."""
        self.conn = connection
        self.is_async = isinstance(connection, psycopg.AsyncConnection)
    
    def _get_cursor(self):
        """Get cursor with dict row factory."""
        return self.conn.cursor(row_factory=dict_row)
    
    # ========================================================================
    # Async Operations
    # ========================================================================
    
    async def get_by_id_async(self, id: int) -> T | None:
        """Get a record by ID."""
        query = f"SELECT * FROM {self.table_name} WHERE id = %s"
        async with self._get_cursor() as cur:
            await cur.execute(query, (id,))
            row = await cur.fetchone()
            if row:
                return self.model_class.model_validate(row)
            return None
    
    async def list_async(
        self,
        limit: int = 100,
        offset: int = 0,
        order_by: str = "id",
        order_desc: bool = False,
    ) -> list[T]:
        """List records with pagination."""
        order = "DESC" if order_desc else "ASC"
        query = f"""
            SELECT * FROM {self.table_name}
            ORDER BY {order_by} {order}
            LIMIT %s OFFSET %s
        """
        async with self._get_cursor() as cur:
            await cur.execute(query, (limit, offset))
            rows = await cur.fetchall()
            return [self.model_class.model_validate(row) for row in rows]
    
    async def count_async(self) -> int:
        """Count total records."""
        query = f"SELECT COUNT(*) as count FROM {self.table_name}"
        async with self._get_cursor() as cur:
            await cur.execute(query)
            row = await cur.fetchone()
            return row["count"] if row else 0
    
    async def delete_async(self, id: int) -> bool:
        """Delete a record by ID."""
        query = f"DELETE FROM {self.table_name} WHERE id = %s RETURNING id"
        async with self._get_cursor() as cur:
            await cur.execute(query, (id,))
            result = await cur.fetchone()
            await self.conn.commit()
            return result is not None
    
    async def exists_async(self, id: int) -> bool:
        """Check if a record exists."""
        query = f"SELECT 1 FROM {self.table_name} WHERE id = %s"
        async with self._get_cursor() as cur:
            await cur.execute(query, (id,))
            return await cur.fetchone() is not None
    
    # ========================================================================
    # Sync Operations (for background jobs)
    # ========================================================================
    
    def get_by_id_sync(self, id: int) -> T | None:
        """Get a record by ID (sync version)."""
        query = f"SELECT * FROM {self.table_name} WHERE id = %s"
        with self._get_cursor() as cur:
            cur.execute(query, (id,))
            row = cur.fetchone()
            if row:
                return self.model_class.model_validate(row)
            return None
    
    def list_sync(
        self,
        limit: int = 100,
        offset: int = 0,
        order_by: str = "id",
        order_desc: bool = False,
    ) -> list[T]:
        """List records with pagination (sync version)."""
        order = "DESC" if order_desc else "ASC"
        query = f"""
            SELECT * FROM {self.table_name}
            ORDER BY {order_by} {order}
            LIMIT %s OFFSET %s
        """
        with self._get_cursor() as cur:
            cur.execute(query, (limit, offset))
            rows = cur.fetchall()
            return [self.model_class.model_validate(row) for row in rows]
    
    def count_sync(self) -> int:
        """Count total records (sync version)."""
        query = f"SELECT COUNT(*) as count FROM {self.table_name}"
        with self._get_cursor() as cur:
            cur.execute(query)
            row = cur.fetchone()
            return row["count"] if row else 0
    
    def delete_sync(self, id: int) -> bool:
        """Delete a record by ID (sync version)."""
        query = f"DELETE FROM {self.table_name} WHERE id = %s RETURNING id"
        with self._get_cursor() as cur:
            cur.execute(query, (id,))
            result = cur.fetchone()
            self.conn.commit()
            return result is not None
