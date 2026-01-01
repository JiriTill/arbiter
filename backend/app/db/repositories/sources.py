"""
Sources repository for game source document management.
"""

from datetime import datetime

from app.db.models import (
    GameSource,
    GameSourceCreate,
    GameSourceWithChunks,
    SourceSuggestion,
    SourceSuggestionCreate,
)
from app.db.repositories.base import BaseRepository


class SourcesRepository(BaseRepository[GameSource, GameSourceCreate]):
    """Repository for game_sources table."""
    
    table_name = "game_sources"
    model_class = GameSource
    
    # ========================================================================
    # Async Methods
    # ========================================================================
    
    async def list_sources(
        self,
        game_id: int | None = None,
        source_type: str | None = None,
        needs_reingest: bool | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[GameSource]:
        """
        List sources with optional filters.
        
        Args:
            game_id: Filter by game
            source_type: Filter by type (rulebook, faq, errata)
            needs_reingest: Filter by reingest flag
            limit: Maximum results
            offset: Pagination offset
            
        Returns:
            List of GameSource objects
        """
        conditions = []
        params: list = []
        
        if game_id is not None:
            conditions.append("game_id = %s")
            params.append(game_id)
        
        if source_type is not None:
            conditions.append("source_type = %s")
            params.append(source_type)
        
        if needs_reingest is not None:
            conditions.append("needs_reingest = %s")
            params.append(needs_reingest)
        
        where_clause = " AND ".join(conditions) if conditions else "TRUE"
        
        query = f"""
            SELECT * FROM game_sources
            WHERE {where_clause}
            ORDER BY game_id, edition
            LIMIT %s OFFSET %s
        """
        params.extend([limit, offset])
        
        async with self._get_cursor() as cur:
            await cur.execute(query, tuple(params))
            rows = await cur.fetchall()
            return [GameSource.model_validate(row) for row in rows]
    
    async def get_source(self, source_id: int) -> GameSource | None:
        """Get a source by ID."""
        return await self.get_by_id_async(source_id)
    
    async def get_sources_for_game(self, game_id: int) -> list[GameSource]:
        """Get all sources for a specific game."""
        query = """
            SELECT * FROM game_sources
            WHERE game_id = %s
            ORDER BY 
                CASE source_type 
                    WHEN 'rulebook' THEN 1
                    WHEN 'faq' THEN 2
                    WHEN 'errata' THEN 3
                    ELSE 4
                END,
                edition
        """
        async with self._get_cursor() as cur:
            await cur.execute(query, (game_id,))
            rows = await cur.fetchall()
            return [GameSource.model_validate(row) for row in rows]
    
    async def create_source(self, source: GameSourceCreate) -> GameSource:
        """Create a new source."""
        query = """
            INSERT INTO game_sources (
                game_id, expansion_id, edition, source_type, source_url,
                is_official, file_hash, needs_ocr, needs_reingest, verified_by
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING *
        """
        async with self._get_cursor() as cur:
            await cur.execute(query, (
                source.game_id,
                source.expansion_id,
                source.edition,
                source.source_type,
                source.source_url,
                source.is_official,
                source.file_hash,
                source.needs_ocr,
                source.needs_reingest,
                source.verified_by,
            ))
            row = await cur.fetchone()
            await self.conn.commit()
            return GameSource.model_validate(row)
    
    async def mark_ingested(self, source_id: int) -> GameSource | None:
        """Mark a source as ingested."""
        query = """
            UPDATE game_sources
            SET last_ingested_at = NOW(), needs_reingest = FALSE, updated_at = NOW()
            WHERE id = %s
            RETURNING *
        """
        async with self._get_cursor() as cur:
            await cur.execute(query, (source_id,))
            row = await cur.fetchone()
            await self.conn.commit()
            if row:
                return GameSource.model_validate(row)
            return None
    
    async def mark_needs_reingest(self, source_id: int) -> bool:
        """Flag a source for re-ingestion."""
        query = """
            UPDATE game_sources
            SET needs_reingest = TRUE, updated_at = NOW()
            WHERE id = %s
            RETURNING id
        """
        async with self._get_cursor() as cur:
            await cur.execute(query, (source_id,))
            result = await cur.fetchone()
            await self.conn.commit()
            return result is not None
    
    async def get_sources_needing_reingest(self, limit: int = 10) -> list[GameSource]:
        """Get sources that need re-ingestion."""
        query = """
            SELECT * FROM game_sources
            WHERE needs_reingest = TRUE
            ORDER BY updated_at ASC
            LIMIT %s
        """
        async with self._get_cursor() as cur:
            await cur.execute(query, (limit,))
            rows = await cur.fetchall()
            return [GameSource.model_validate(row) for row in rows]
    
    async def update_file_hash(self, source_id: int, file_hash: str) -> bool:
        """Update the file hash for a source."""
        query = """
            UPDATE game_sources
            SET file_hash = %s, updated_at = NOW()
            WHERE id = %s
            RETURNING id
        """
        async with self._get_cursor() as cur:
            await cur.execute(query, (file_hash, source_id))
            result = await cur.fetchone()
            await self.conn.commit()
            return result is not None

    async def create_suggestion(self, suggestion: SourceSuggestionCreate) -> SourceSuggestion:
        """Create a new source suggestion."""
        query = """
            INSERT INTO source_suggestions (
                game_id, suggested_url, user_note, status
            )
            VALUES (
                %(game_id)s, %(suggested_url)s, %(user_note)s, 'pending'
            )
            RETURNING id, created_at, updated_at
        """
        async with self._get_cursor() as cur:
            await cur.execute(query, suggestion.model_dump())
            row = await cur.fetchone()
            await self.conn.commit()
            
            return SourceSuggestion(
                id=row["id"],
                status="pending",
                created_at=row["created_at"],
                updated_at=row["updated_at"],
                **suggestion.model_dump()
            )
    
    # ========================================================================
    # Sync Methods (for background jobs)
    # ========================================================================
    
    def get_source_sync(self, source_id: int) -> GameSource | None:
        """Get a source by ID (sync version)."""
        return self.get_by_id_sync(source_id)
    
    def get_sources_needing_reingest_sync(self, limit: int = 10) -> list[GameSource]:
        """Get sources needing reingest (sync version)."""
        query = """
            SELECT * FROM game_sources
            WHERE needs_reingest = TRUE
            ORDER BY updated_at ASC
            LIMIT %s
        """
        with self._get_cursor() as cur:
            cur.execute(query, (limit,))
            rows = cur.fetchall()
            return [GameSource.model_validate(row) for row in rows]
    
    def mark_ingested_sync(self, source_id: int) -> GameSource | None:
        """Mark as ingested (sync version)."""
        query = """
            UPDATE game_sources
            SET last_ingested_at = NOW(), needs_reingest = FALSE, updated_at = NOW()
            WHERE id = %s
            RETURNING *
        """
        with self._get_cursor() as cur:
            cur.execute(query, (source_id,))
            row = cur.fetchone()
            self.conn.commit()
            if row:
                return GameSource.model_validate(row)
            return None
    
    async def sources_are_indexed(self, source_ids: list[int]) -> bool:
        """
        Check if all sources have valid, non-expired chunks with embeddings.
        
        Args:
            source_ids: List of source IDs to check
            
        Returns:
            True if all sources have at least one valid chunk with embedding
        """
        if not source_ids:
            return False
        
        placeholders = ", ".join(["%s"] * len(source_ids))
        
        # Check if each source has at least one chunk with embedding that hasn't expired
        query = f"""
            SELECT 
                gs.id as source_id,
                COUNT(rc.id) as chunk_count
            FROM game_sources gs
            LEFT JOIN rule_chunks rc ON rc.source_id = gs.id 
                AND rc.embedding IS NOT NULL
                AND (rc.expires_at IS NULL OR rc.expires_at > NOW())
            WHERE gs.id IN ({placeholders})
            GROUP BY gs.id
        """
        
        async with self._get_cursor() as cur:
            await cur.execute(query, tuple(source_ids))
            rows = await cur.fetchall()
            
            # Convert to dict for easy lookup
            chunk_counts = {row["source_id"]: row["chunk_count"] for row in rows}
            
            # All source_ids must be present and have at least 1 chunk
            for sid in source_ids:
                if sid not in chunk_counts or chunk_counts[sid] == 0:
                    return False
            
            return True
    
    async def get_unindexed_source_ids(self, source_ids: list[int]) -> list[int]:
        """
        Get list of source IDs that don't have valid indexed chunks.
        
        Args:
            source_ids: List of source IDs to check
            
        Returns:
            List of source IDs that need indexing
        """
        if not source_ids:
            return []
        
        placeholders = ", ".join(["%s"] * len(source_ids))
        
        query = f"""
            SELECT 
                gs.id as source_id,
                COUNT(rc.id) as chunk_count
            FROM game_sources gs
            LEFT JOIN rule_chunks rc ON rc.source_id = gs.id 
                AND rc.embedding IS NOT NULL
                AND (rc.expires_at IS NULL OR rc.expires_at > NOW())
            WHERE gs.id IN ({placeholders})
            GROUP BY gs.id
        """
        
        async with self._get_cursor() as cur:
            await cur.execute(query, tuple(source_ids))
            rows = await cur.fetchall()
            
            # Convert to dict
            chunk_counts = {row["source_id"]: row["chunk_count"] for row in rows}
            
            # Return IDs with 0 chunks (or not found)
            unindexed = []
            for sid in source_ids:
                if sid not in chunk_counts or chunk_counts[sid] == 0:
                    unindexed.append(sid)
            
            return unindexed

