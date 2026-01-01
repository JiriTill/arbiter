"""
Database module with connection management and FastAPI integration.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

import psycopg

from app.db.connection import (
    get_async_connection,
    get_async_cursor,
    get_async_pool,
    close_async_pool,
    get_sync_connection,
    get_sync_cursor,
    check_database_connection,
    test_connection,
)
from app.db.models import (
    Game, GameCreate, GameWithSources,
    Expansion, ExpansionCreate,
    GameSource, GameSourceCreate,
    RuleChunk, RuleChunkCreate, RuleChunkSearchResult,
    AskHistory, AskHistoryCreate, AskHistoryWithGame,
    AnswerFeedback, AnswerFeedbackCreate,
    SourceHealth, SourceHealthCreate,
    Citation,
)
from app.db.repositories import (
    GamesRepository,
    SourcesRepository,
    ChunksRepository,
    HistoryRepository,
    FeedbackRepository,
    CostsRepository,
)
from app.db.repositories.costs import CostsRepository


# ============================================================================
# FastAPI Lifespan
# ============================================================================

@asynccontextmanager
async def db_lifespan(app):
    """
    Database lifespan context manager for FastAPI.
    
    Usage in main.py:
        from app.db import db_lifespan
        
        app = FastAPI(lifespan=db_lifespan)
    """
    # Startup: Initialize connection pool
    try:
        pool = await get_async_pool()
        print("✓ Database connection pool initialized")
    except Exception as e:
        print(f"⚠ Database connection failed: {e}")
    
    yield
    
    # Shutdown: Close connection pool
    await close_async_pool()
    print("✓ Database connection pool closed")


# ============================================================================
# FastAPI Dependencies
# ============================================================================

async def get_db() -> AsyncGenerator[psycopg.AsyncConnection, None]:
    """
    FastAPI dependency for database connection.
    
    Usage in routes:
        @router.get("/games")
        async def list_games(db: AsyncConnection = Depends(get_db)):
            repo = GamesRepository(db)
            return await repo.list_games()
    """
    async with get_async_connection() as conn:
        yield conn


async def get_games_repo() -> AsyncGenerator[GamesRepository, None]:
    """FastAPI dependency for GamesRepository."""
    async with get_async_connection() as conn:
        yield GamesRepository(conn)


async def get_sources_repo() -> AsyncGenerator[SourcesRepository, None]:
    """FastAPI dependency for SourcesRepository."""
    async with get_async_connection() as conn:
        yield SourcesRepository(conn)


async def get_chunks_repo() -> AsyncGenerator[ChunksRepository, None]:
    """FastAPI dependency for ChunksRepository."""
    async with get_async_connection() as conn:
        yield ChunksRepository(conn)


async def get_history_repo() -> AsyncGenerator[HistoryRepository, None]:
    """FastAPI dependency for HistoryRepository."""
    async with get_async_connection() as conn:
        yield HistoryRepository(conn)


async def get_feedback_repo() -> AsyncGenerator[FeedbackRepository, None]:
    """FastAPI dependency for FeedbackRepository."""
    async with get_async_connection() as conn:
        yield FeedbackRepository(conn)


async def get_costs_repo() -> AsyncGenerator[CostsRepository, None]:
    """FastAPI dependency for CostsRepository."""
    async with get_async_connection() as conn:
        yield CostsRepository(conn)


# ============================================================================
# Exports
# ============================================================================

__all__ = [
    # Connection
    "get_async_connection",
    "get_async_cursor",
    "get_sync_connection",
    "get_sync_cursor",
    "check_database_connection",
    "test_connection",
    
    # FastAPI integration
    "db_lifespan",
    "get_db",
    "get_games_repo",
    "get_sources_repo",
    "get_chunks_repo",
    "get_history_repo",
    "get_feedback_repo",
    "get_costs_repo",
    
    # Models
    "Game", "GameCreate", "GameWithSources",
    "Expansion", "ExpansionCreate",
    "GameSource", "GameSourceCreate",
    "RuleChunk", "RuleChunkCreate", "RuleChunkSearchResult",
    "AskHistory", "AskHistoryCreate", "AskHistoryWithGame",
    "AnswerFeedback", "AnswerFeedbackCreate",
    "SourceHealth", "SourceHealthCreate",
    "Citation",
    
    # Repositories
    "GamesRepository",
    "SourcesRepository",
    "ChunksRepository",
    "HistoryRepository",
    "FeedbackRepository",
    "CostsRepository",
]
