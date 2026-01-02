"""
Database connection management using psycopg3.
Provides both sync and async connection pooling.
"""

from contextlib import asynccontextmanager, contextmanager
from typing import AsyncGenerator, Generator

import psycopg
from psycopg_pool import AsyncConnectionPool, ConnectionPool

from app.config import get_settings


# Global connection pools
_async_pool: AsyncConnectionPool | None = None
_sync_pool: ConnectionPool | None = None


# ============================================================================
# Async Connection Pool
# ============================================================================

async def get_async_pool() -> AsyncConnectionPool:
    """Get or create the async connection pool."""
    global _async_pool
    if _async_pool is None:
        settings = get_settings()
        if not settings.database_url:
            raise ValueError("DATABASE_URL not configured")
        
        _async_pool = AsyncConnectionPool(
            settings.database_url,
            min_size=2,
            max_size=10,
            open=False,
            kwargs={"prepare_threshold": None}  # Disable prepared statements for transaction pooler
        )
        await _async_pool.open()
    return _async_pool


async def close_async_pool():
    """Close the async connection pool."""
    global _async_pool
    if _async_pool is not None:
        await _async_pool.close()
        _async_pool = None


@asynccontextmanager
async def get_async_connection() -> AsyncGenerator[psycopg.AsyncConnection, None]:
    """
    Get an async database connection from the pool.
    
    Usage:
        async with get_async_connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT * FROM games")
                results = await cur.fetchall()
    """
    pool = await get_async_pool()
    async with pool.connection() as conn:
        yield conn


@asynccontextmanager
async def get_async_cursor():
    """Get an async database cursor (convenience wrapper)."""
    async with get_async_connection() as conn:
        async with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
            yield cur


# ============================================================================
# Sync Connection Pool (for background jobs)
# ============================================================================

def get_sync_pool() -> ConnectionPool:
    """Get or create the sync connection pool."""
    global _sync_pool
    if _sync_pool is None:
        settings = get_settings()
        if not settings.database_url:
            raise ValueError("DATABASE_URL not configured")
        
        _sync_pool = ConnectionPool(
            settings.database_url,
            min_size=1,
            max_size=5,
            open=True,
            kwargs={"prepare_threshold": None}  # Disable prepared statements for transaction pooler
        )
    return _sync_pool


def close_sync_pool():
    """Close the sync connection pool."""
    global _sync_pool
    if _sync_pool is not None:
        _sync_pool.close()
        _sync_pool = None


@contextmanager
def get_sync_connection() -> Generator[psycopg.Connection, None, None]:
    """Get a sync database connection from the pool."""
    pool = get_sync_pool()
    with pool.connection() as conn:
        yield conn


@contextmanager
def get_sync_cursor():
    """Get a sync database cursor (convenience wrapper)."""
    with get_sync_connection() as conn:
        with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
            yield cur


# ============================================================================
# Health Check
# ============================================================================

async def check_database_connection() -> bool:
    """
    Check if database connection is working.
    Returns True if connection succeeds, False otherwise.
    """
    try:
        async with get_async_cursor() as cur:
            await cur.execute("SELECT 1 as health")
            result = await cur.fetchone()
            return result is not None and result.get("health") == 1
    except Exception as e:
        print(f"Database connection error: {e}")
        return False


def test_connection():
    """Synchronous connection test for CLI usage."""
    try:
        with get_sync_cursor() as cur:
            cur.execute("SELECT 1 as health")
            result = cur.fetchone()
            if result and result.get("health") == 1:
                print("✓ Database connection successful")
                
                # Also check for vector extension
                cur.execute("SELECT extname FROM pg_extension WHERE extname = 'vector'")
                vector_ext = cur.fetchone()
                if vector_ext:
                    print("✓ pgvector extension enabled")
                else:
                    print("⚠ pgvector extension not found")
                
                return True
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        return False
