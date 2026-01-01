"""
Chunks repository for rule chunk management and vector search.
"""

from datetime import datetime

from app.db.models import RuleChunk, RuleChunkCreate, RuleChunkSearchResult
from app.db.repositories.base import BaseRepository


class ChunksRepository(BaseRepository[RuleChunk, RuleChunkCreate]):
    """Repository for rule_chunks table with vector search capabilities."""
    
    table_name = "rule_chunks"
    model_class = RuleChunk
    
    # ========================================================================
    # Vector Search Methods
    # ========================================================================
    
    async def vector_search(
        self,
        embedding: list[float],
        game_id: int | None = None,
        source_ids: list[int] | None = None,
        limit: int = 5,
        min_similarity: float = 0.5,
    ) -> list[RuleChunkSearchResult]:
        """
        Perform vector similarity search on rule chunks.
        
        Args:
            embedding: Query embedding (1536 dimensions)
            game_id: Optional filter by game
            source_ids: Optional filter by specific sources
            limit: Maximum results to return
            min_similarity: Minimum cosine similarity threshold
            
        Returns:
            List of chunks with similarity scores
        """
        # Build the query with optional filters
        conditions = ["rc.embedding IS NOT NULL"]
        params: list = []
        
        if game_id is not None:
            conditions.append("gs.game_id = %s")
            params.append(game_id)
        
        if source_ids:
            placeholders = ", ".join(["%s"] * len(source_ids))
            conditions.append(f"rc.source_id IN ({placeholders})")
            params.extend(source_ids)
        
        # Filter out expired chunks
        conditions.append("(rc.expires_at IS NULL OR rc.expires_at > NOW())")
        
        where_clause = " AND ".join(conditions)
        
        # Add embedding and limit params
        embedding_str = "[" + ",".join(map(str, embedding)) + "]"
        params.append(embedding_str)
        params.append(min_similarity)
        params.append(limit)
        
        query = f"""
            SELECT 
                rc.*,
                1 - (rc.embedding <=> %s::vector) as similarity,
                gs.edition as source_edition,
                g.name as game_name
            FROM rule_chunks rc
            JOIN game_sources gs ON rc.source_id = gs.id
            JOIN games g ON gs.game_id = g.id
            WHERE {where_clause}
            AND 1 - (rc.embedding <=> %s::vector) >= %s
            ORDER BY rc.embedding <=> %s::vector
            LIMIT %s
        """
        
        # Add embedding again for ORDER BY
        params.insert(-1, embedding_str)
        
        async with self._get_cursor() as cur:
            await cur.execute(query, tuple(params))
            rows = await cur.fetchall()
            return [RuleChunkSearchResult.model_validate(row) for row in rows]
    
    async def hybrid_search(
        self,
        embedding: list[float],
        keywords: list[str],
        game_id: int | None = None,
        source_ids: list[int] | None = None,
        limit: int = 5,
        vector_weight: float = 0.7,
    ) -> list[RuleChunkSearchResult]:
        """
        Hybrid search combining vector similarity and keyword matching.
        
        Args:
            embedding: Query embedding
            keywords: Keywords to match in text
            game_id: Optional game filter
            source_ids: Optional source filter
            limit: Maximum results
            vector_weight: Weight for vector score (0-1), keyword gets 1-vector_weight
            
        Returns:
            List of chunks with combined scores
        """
        # Build keyword conditions
        keyword_conditions = []
        for kw in keywords:
            keyword_conditions.append(f"rc.chunk_text ILIKE %s")
        
        conditions = ["rc.embedding IS NOT NULL"]
        params: list = []
        
        if game_id is not None:
            conditions.append("gs.game_id = %s")
            params.append(game_id)
        
        if source_ids:
            placeholders = ", ".join(["%s"] * len(source_ids))
            conditions.append(f"rc.source_id IN ({placeholders})")
            params.extend(source_ids)
        
        conditions.append("(rc.expires_at IS NULL OR rc.expires_at > NOW())")
        
        where_clause = " AND ".join(conditions)
        
        # Add keyword patterns
        keyword_patterns = [f"%{kw}%" for kw in keywords]
        
        embedding_str = "[" + ",".join(map(str, embedding)) + "]"
        
        # Build the hybrid query
        if keywords:
            keyword_match_expr = " OR ".join([f"rc.chunk_text ILIKE %s" for _ in keywords])
            keyword_score = f"CASE WHEN ({keyword_match_expr}) THEN 1.0 ELSE 0.0 END"
            
            query = f"""
                SELECT 
                    rc.*,
                    (1 - (rc.embedding <=> %s::vector)) as vector_similarity,
                    {keyword_score} as keyword_match,
                    ((1 - (rc.embedding <=> %s::vector)) * %s + 
                     {keyword_score} * %s) as combined_score,
                    gs.edition as source_edition,
                    g.name as game_name
                FROM rule_chunks rc
                JOIN game_sources gs ON rc.source_id = gs.id
                JOIN games g ON gs.game_id = g.id
                WHERE {where_clause}
                ORDER BY combined_score DESC
                LIMIT %s
            """
            
            query_params = list(params)
            query_params.append(embedding_str)  # for vector similarity
            query_params.extend(keyword_patterns)  # for keyword case 1
            query_params.append(embedding_str)  # for combined score vector part
            query_params.append(vector_weight)
            query_params.extend(keyword_patterns)  # for keyword case 2
            query_params.append(1 - vector_weight)
            query_params.append(limit)
        else:
            # Fall back to pure vector search
            return await self.vector_search(embedding, game_id, source_ids, limit)
        
        async with self._get_cursor() as cur:
            await cur.execute(query, tuple(query_params))
            rows = await cur.fetchall()
            # Use combined_score as similarity for the result model
            results = []
            for row in rows:
                row_dict = dict(row)
                row_dict["similarity"] = row_dict.pop("combined_score", row_dict.get("vector_similarity", 0))
                results.append(RuleChunkSearchResult.model_validate(row_dict))
            return results
    
    async def keyword_search(
        self,
        query: str,
        source_ids: list[int] | None = None,
        game_id: int | None = None,
        limit: int = 30,
    ) -> list[tuple[RuleChunk, float]]:
        """
        Full-text keyword search using PostgreSQL tsvector.
        
        Uses the tsv column (GIN indexed) for efficient text search.
        Results are ranked by ts_rank_cd for relevance.
        
        Args:
            query: Natural language search query
            source_ids: Optional filter by specific sources
            game_id: Optional filter by game
            limit: Maximum results to return
            
        Returns:
            List of (chunk, relevance_score) tuples
        """
        # Build filter conditions
        conditions = ["rc.tsv IS NOT NULL"]
        params: list = []
        
        if game_id is not None:
            conditions.append("gs.game_id = %s")
            params.append(game_id)
        
        if source_ids:
            placeholders = ", ".join(["%s"] * len(source_ids))
            conditions.append(f"rc.source_id IN ({placeholders})")
            params.extend(source_ids)
        
        # Filter out expired chunks
        conditions.append("(rc.expires_at IS NULL OR rc.expires_at > NOW())")
        
        where_clause = " AND ".join(conditions)
        
        # Add query for tsquery conversion
        params.append(query)
        params.append(query)
        params.append(limit)
        
        # Use websearch_to_tsquery for natural language parsing
        # Falls back to plainto_tsquery if websearch fails
        search_query = """
            SELECT 
                rc.*,
                ts_rank_cd(rc.tsv, websearch_to_tsquery('english', %s)) as rank
            FROM rule_chunks rc
            JOIN game_sources gs ON rc.source_id = gs.id
            JOIN games g ON gs.game_id = g.id
            WHERE {where_clause}
            AND rc.tsv @@ websearch_to_tsquery('english', %s)
            ORDER BY rank DESC, rc.page_number ASC
            LIMIT %s
        """.format(where_clause=where_clause)
        
        async with self._get_cursor() as cur:
            try:
                await cur.execute(search_query, tuple(params))
                rows = await cur.fetchall()
            except Exception:
                # Fallback to plainto_tsquery if websearch fails
                fallback_query = """
                    SELECT 
                        rc.*,
                        ts_rank_cd(rc.tsv, plainto_tsquery('english', %s)) as rank
                    FROM rule_chunks rc
                    JOIN game_sources gs ON rc.source_id = gs.id
                    JOIN games g ON gs.game_id = g.id
                    WHERE {where_clause}
                    AND rc.tsv @@ plainto_tsquery('english', %s)
                    ORDER BY rank DESC, rc.page_number ASC
                    LIMIT %s
                """.format(where_clause=where_clause)
                await cur.execute(fallback_query, tuple(params))
                rows = await cur.fetchall()
            
            results = []
            for row in rows:
                row_dict = dict(row)
                rank = row_dict.pop("rank", 0.0)
                chunk = RuleChunk.model_validate(row_dict)
                results.append((chunk, float(rank)))
            return results
    
    def keyword_search_sync(
        self,
        query: str,
        source_ids: list[int] | None = None,
        limit: int = 30,
    ) -> list[tuple[RuleChunk, float]]:
        """
        Synchronous version of keyword_search for use in background jobs.
        
        Args:
            query: Natural language search query
            source_ids: Optional filter by specific sources
            limit: Maximum results to return
            
        Returns:
            List of (chunk, relevance_score) tuples
        """
        from app.db.connection import get_sync_connection
        
        conditions = ["tsv IS NOT NULL"]
        params: list = []
        
        if source_ids:
            placeholders = ", ".join(["%s"] * len(source_ids))
            conditions.append(f"source_id IN ({placeholders})")
            params.extend(source_ids)
        
        conditions.append("(expires_at IS NULL OR expires_at > NOW())")
        where_clause = " AND ".join(conditions)
        
        params.append(query)
        params.append(query)
        params.append(limit)
        
        search_query = f"""
            SELECT 
                *,
                ts_rank_cd(tsv, plainto_tsquery('english', %s)) as rank
            FROM rule_chunks
            WHERE {where_clause}
            AND tsv @@ plainto_tsquery('english', %s)
            ORDER BY rank DESC, page_number ASC
            LIMIT %s
        """
        
        with get_sync_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(search_query, tuple(params))
                rows = cur.fetchall()
                
                results = []
                for row in rows:
                    row_dict = dict(row)
                    rank = row_dict.pop("rank", 0.0)
                    chunk = RuleChunk.model_validate(row_dict)
                    results.append((chunk, float(rank)))
                return results
    
    # ========================================================================
    # CRUD Methods
    # ========================================================================
    
    async def get_chunks_by_source(
        self,
        source_id: int,
        limit: int = 1000,
    ) -> list[RuleChunk]:
        """Get all chunks for a source."""
        query = """
            SELECT * FROM rule_chunks
            WHERE source_id = %s
            ORDER BY page_number, chunk_index
            LIMIT %s
        """
        async with self._get_cursor() as cur:
            await cur.execute(query, (source_id, limit))
            rows = await cur.fetchall()
            return [RuleChunk.model_validate(row) for row in rows]
    
    async def create_chunk(self, chunk: RuleChunkCreate) -> RuleChunk:
        """Create a new chunk with embedding."""
        embedding_value = None
        if chunk.embedding:
            embedding_value = "[" + ",".join(map(str, chunk.embedding)) + "]"
        
        query = """
            INSERT INTO rule_chunks (
                source_id, page_number, chunk_index, section_title, chunk_text,
                embedding, precedence_level, overrides_chunk_id, override_confidence,
                phase_tags, expires_at
            )
            VALUES (%s, %s, %s, %s, %s, %s::vector, %s, %s, %s, %s, %s)
            RETURNING id, source_id, page_number, chunk_index, section_title, 
                      chunk_text, precedence_level, overrides_chunk_id, 
                      override_confidence, phase_tags, expires_at, created_at
        """
        async with self._get_cursor() as cur:
            await cur.execute(query, (
                chunk.source_id,
                chunk.page_number,
                chunk.chunk_index,
                chunk.section_title,
                chunk.chunk_text,
                embedding_value,
                chunk.precedence_level,
                chunk.overrides_chunk_id,
                chunk.override_confidence,
                chunk.phase_tags,
                chunk.expires_at,
            ))
            row = await cur.fetchone()
            await self.conn.commit()
            return RuleChunk.model_validate(row)
    
    async def create_chunks_batch(self, chunks: list[RuleChunkCreate]) -> int:
        """
        Batch create chunks for efficiency.
        
        Returns:
            Number of chunks created
        """
        if not chunks:
            return 0
        
        count = 0
        for chunk in chunks:
            await self.create_chunk(chunk)
            count += 1
        
        return count
    
    async def delete_chunks_by_source(self, source_id: int) -> int:
        """Delete all chunks for a source (before re-ingestion)."""
        query = """
            DELETE FROM rule_chunks
            WHERE source_id = %s
            RETURNING id
        """
        async with self._get_cursor() as cur:
            await cur.execute(query, (source_id,))
            rows = await cur.fetchall()
            await self.conn.commit()
            return len(rows)
    
    async def cleanup_expired(self) -> int:
        """Remove expired chunks."""
        query = """
            DELETE FROM rule_chunks
            WHERE expires_at IS NOT NULL AND expires_at < NOW()
            RETURNING id
        """
        async with self._get_cursor() as cur:
            await cur.execute(query)
            rows = await cur.fetchall()
            await self.conn.commit()
            return len(rows)
    
    # ========================================================================
    # Sync Methods (for background jobs)
    # ========================================================================
    
    def create_chunk_sync(self, chunk: RuleChunkCreate) -> RuleChunk:
        """Create chunk (sync version)."""
        embedding_value = None
        if chunk.embedding:
            embedding_value = "[" + ",".join(map(str, chunk.embedding)) + "]"
        
        query = """
            INSERT INTO rule_chunks (
                source_id, page_number, chunk_index, section_title, chunk_text,
                embedding, precedence_level, overrides_chunk_id, override_confidence,
                phase_tags, expires_at
            )
            VALUES (%s, %s, %s, %s, %s, %s::vector, %s, %s, %s, %s, %s)
            RETURNING id, source_id, page_number, chunk_index, section_title, 
                      chunk_text, precedence_level, overrides_chunk_id, 
                      override_confidence, phase_tags, expires_at, created_at
        """
        with self._get_cursor() as cur:
            cur.execute(query, (
                chunk.source_id,
                chunk.page_number,
                chunk.chunk_index,
                chunk.section_title,
                chunk.chunk_text,
                embedding_value,
                chunk.precedence_level,
                chunk.overrides_chunk_id,
                chunk.override_confidence,
                chunk.phase_tags,
                chunk.expires_at,
            ))
            row = cur.fetchone()
            self.conn.commit()
            return RuleChunk.model_validate(row)
    
    def delete_chunks_by_source_sync(self, source_id: int) -> int:
        """Delete chunks by source (sync version)."""
        query = "DELETE FROM rule_chunks WHERE source_id = %s RETURNING id"
        with self._get_cursor() as cur:
            cur.execute(query, (source_id,))
            rows = cur.fetchall()
            self.conn.commit()
            return len(rows)
    
    def bulk_insert_chunks_sync(self, chunks: list[RuleChunkCreate]) -> int:
        """
        Bulk insert chunks for efficiency.
        Uses executemany for better performance with large batches.
        
        Args:
            chunks: List of RuleChunkCreate objects
            
        Returns:
            Number of chunks inserted
        """
        if not chunks:
            return 0
        
        query = """
            INSERT INTO rule_chunks (
                source_id, page_number, chunk_index, section_title, chunk_text,
                embedding, precedence_level, overrides_chunk_id, override_confidence,
                phase_tags, expires_at
            )
            VALUES (%s, %s, %s, %s, %s, %s::vector, %s, %s, %s, %s, %s)
        """
        
        values = []
        for chunk in chunks:
            embedding_value = None
            if chunk.embedding:
                embedding_value = "[" + ",".join(map(str, chunk.embedding)) + "]"
            
            values.append((
                chunk.source_id,
                chunk.page_number,
                chunk.chunk_index,
                chunk.section_title,
                chunk.chunk_text,
                embedding_value,
                chunk.precedence_level,
                chunk.overrides_chunk_id,
                chunk.override_confidence,
                chunk.phase_tags,
                chunk.expires_at,
            ))
        
        with self._get_cursor() as cur:
            cur.executemany(query, values)
            self.conn.commit()
        
        return len(chunks)
