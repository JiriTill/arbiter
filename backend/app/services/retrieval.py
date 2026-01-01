"""
Hybrid retrieval service combining keyword and vector search.
"""

import asyncio
import logging
from dataclasses import dataclass
from typing import Any

from app.db.models import RuleChunk, RuleChunkSearchResult
from app.db.repositories.chunks import ChunksRepository
from app.services.cache import get_or_create_embedding


logger = logging.getLogger(__name__)


# Weights for combining scores
KEYWORD_WEIGHT = 0.4
VECTOR_WEIGHT = 0.6


@dataclass
class ScoredChunk:
    """Chunk with scoring information."""
    chunk: RuleChunk | RuleChunkSearchResult
    bm25_score: float
    vec_score: float
    final_score: float
    
    @property
    def id(self) -> int:
        return self.chunk.id


def normalize_scores(scores: list[float]) -> list[float]:
    """
    Apply min-max normalization to scores.
    
    Args:
        scores: List of raw scores
        
    Returns:
        List of normalized scores (0-1 range)
    """
    if not scores:
        return []
    
    min_score = min(scores)
    max_score = max(scores)
    
    if max_score == min_score:
        return [1.0] * len(scores)  # All same, give max score
    
    return [(s - min_score) / (max_score - min_score) for s in scores]


async def hybrid_search(
    query: str,
    source_ids: list[int],
    chunks_repo: ChunksRepository,
    game_id: int | None = None,
    expansion_ids: list[int] | None = None,
    keyword_limit: int = 30,
    vector_limit: int = 30,
    final_limit: int = 12,
    expand_top_k: int = 5,
    detect_conflicts: bool = True,
) -> tuple[list[RuleChunk | RuleChunkSearchResult], dict[str, Any] | None]:
    """
    Hybrid search combining BM25 keyword search and vector similarity.
    
    Algorithm:
    1. Run keyword search and vector search in parallel
    2. Merge results by chunk_id
    3. Normalize scores using min-max normalization
    4. Combine with weighted sum (40% keyword, 60% vector)
    5. Apply precedence boosting
    6. Sort by final score
    7. Check for conflicts
    8. Expand top-k results with adjacent chunks
    
    Args:
        query: User's search query
        source_ids: List of source IDs to search within
        chunks_repo: ChunksRepository instance
        game_id: Optional game ID filter
        expansion_ids: List of enabled expansion IDs in priority order
        keyword_limit: Max results from keyword search
        vector_limit: Max results from vector search
        final_limit: Max chunks before adjacency expansion
        expand_top_k: Number of top results to expand with neighbors
        detect_conflicts: Whether to check for rule conflicts
        
    Returns:
        Tuple of (ranked chunks, conflict info if detected)
    """
    logger.info(f"Hybrid search: query='{query[:50]}...', sources={source_ids}, expansions={expansion_ids}")
    
    enabled_expansions = set(expansion_ids or [])
    expansion_priority = {exp_id: idx for idx, exp_id in enumerate(expansion_ids or [])}
    
    # ========================================================================
    # Step 1: Run searches in parallel
    # ========================================================================
    
    # Get embedding (cached)
    query_embedding = get_or_create_embedding(query)
    
    # Run both searches concurrently
    keyword_task = chunks_repo.keyword_search(
        query=query,
        source_ids=source_ids,
        game_id=game_id,
        limit=keyword_limit,
    )
    
    vector_task = chunks_repo.vector_search(
        embedding=query_embedding,
        source_ids=source_ids,
        limit=vector_limit,
        min_similarity=0.3,
    )
    
    try:
        kw_results, vec_results = await asyncio.gather(keyword_task, vector_task)
    except Exception as e:
        logger.error(f"Search failed: {e}")
        # Fallback to vector-only if keyword search fails
        try:
            vec_results = await vector_task
            kw_results = []
        except Exception:
            return [], None
    
    logger.debug(f"Keyword hits: {len(kw_results)}, Vector hits: {len(vec_results)}")
    
    # ========================================================================
    # Step 2: Merge and collect scores
    # ========================================================================
    
    all_chunks: dict[int, dict[str, Any]] = {}
    
    # Add keyword results
    for chunk, score in kw_results:
        chunk_id = chunk.id
        all_chunks[chunk_id] = {
            "chunk": chunk,
            "bm25_score": score,
            "vec_score": 0.0,
        }
    
    # Add/merge vector results
    for chunk_result in vec_results:
        chunk_id = chunk_result.id
        score = chunk_result.similarity
        
        if chunk_id in all_chunks:
            all_chunks[chunk_id]["vec_score"] = score
        else:
            all_chunks[chunk_id] = {
                "chunk": chunk_result,
                "bm25_score": 0.0,
                "vec_score": score,
            }
    
    if not all_chunks:
        logger.warning("No results from either search")
        return [], None
    
    # ========================================================================
    # Step 3: Normalize scores
    # ========================================================================
    
    bm25_scores = [d["bm25_score"] for d in all_chunks.values()]
    vec_scores = [d["vec_score"] for d in all_chunks.values()]
    
    bm25_norm = normalize_scores(bm25_scores)
    vec_norm = normalize_scores(vec_scores)
    
    # ========================================================================
    # Step 4: Calculate final scores with precedence boosting
    # ========================================================================
    
    scored_chunks: list[ScoredChunk] = []
    
    for i, (chunk_id, data) in enumerate(all_chunks.items()):
        chunk = data["chunk"]
        base_score = (KEYWORD_WEIGHT * bm25_norm[i]) + (VECTOR_WEIGHT * vec_norm[i])
        
        # Apply precedence boost
        precedence_boost = calculate_precedence_boost(
            chunk=chunk,
            enabled_expansions=enabled_expansions,
            expansion_priority=expansion_priority,
        )
        
        final_score = base_score + precedence_boost
        
        scored_chunks.append(ScoredChunk(
            chunk=chunk,
            bm25_score=data["bm25_score"],
            vec_score=data["vec_score"],
            final_score=final_score,
        ))
    
    # Sort by final score
    scored_chunks.sort(key=lambda x: x.final_score, reverse=True)
    
    logger.debug(f"Total unique chunks: {len(scored_chunks)}")
    
    # ========================================================================
    # Step 5: Check for conflicts
    # ========================================================================
    
    conflict_info = None
    if detect_conflicts and len(scored_chunks) >= 2:
        from app.services.conflict_detector import check_top_chunks_for_conflict
        conflict_info = check_top_chunks_for_conflict(
            ranked_chunks=scored_chunks[:5],
            question=query,
            score_threshold=0.05,
        )
    
    # Take top results
    top_chunks = scored_chunks[:final_limit]
    
    # ========================================================================
    # Step 6: Adjacency expansion
    # ========================================================================
    
    final_chunks = await expand_with_neighbors(
        top_chunks=top_chunks[:expand_top_k],
        all_candidates=scored_chunks,
        chunks_repo=chunks_repo,
    )
    
    # Add remaining top chunks that weren't expanded
    seen_ids = {c.id for c in final_chunks}
    for sc in top_chunks[expand_top_k:]:
        if sc.chunk.id not in seen_ids:
            final_chunks.append(sc.chunk)
            seen_ids.add(sc.chunk.id)
    
    logger.info(f"Hybrid search returned {len(final_chunks)} chunks, conflict={'yes' if conflict_info else 'no'}")
    
    return final_chunks, conflict_info


def calculate_precedence_boost(
    chunk: RuleChunk | RuleChunkSearchResult,
    enabled_expansions: set[int],
    expansion_priority: dict[int, int],
) -> float:
    """
    Calculate precedence boost for a chunk.
    
    Boost values:
    - Errata/FAQ (level 3): +0.15
    - Enabled expansion (level 2): +0.10 - (priority * 0.01)
    - Base rules (level 1): +0.00
    
    Args:
        chunk: The chunk to boost
        enabled_expansions: Set of enabled expansion IDs
        expansion_priority: Dict mapping expansion_id -> priority index (0 = highest)
        
    Returns:
        Boost value to add to score
    """
    precedence_level = getattr(chunk, 'precedence_level', 1)
    expansion_id = getattr(chunk, 'expansion_id', None)
    
    # Errata/FAQ always gets highest boost
    if precedence_level == 3:
        return 0.15
    
    # Expansion content
    if precedence_level == 2:
        if expansion_id and expansion_id in enabled_expansions:
            # Enabled expansion - boost based on user priority
            priority_index = expansion_priority.get(expansion_id, 99)
            # Higher priority (lower index) = higher boost
            # Max boost 0.10, reduced by 0.01 for each priority level
            boost = 0.10 - (priority_index * 0.01)
            return max(boost, 0.05)  # Minimum 0.05 for enabled expansions
        else:
            # Expansion not enabled - slight penalty
            return -0.05
    
    # Base rules (level 1)
    return 0.0


async def expand_with_neighbors(
    top_chunks: list[ScoredChunk],
    all_candidates: list[ScoredChunk],
    chunks_repo: ChunksRepository,
) -> list[RuleChunk | RuleChunkSearchResult]:
    """
    Expand top chunks with their neighbors (chunk_index ± 1).
    
    This helps capture context that spans multiple chunks.
    
    Args:
        top_chunks: Top scored chunks to expand
        all_candidates: All candidate chunks (may contain neighbors)
        chunks_repo: Repository for fetching neighbors
        
    Returns:
        Expanded list of chunks
    """
    result_chunks = []
    seen_ids = set()
    
    # Build index of candidates by (source_id, chunk_index)
    candidate_index: dict[tuple[int, int], RuleChunk | RuleChunkSearchResult] = {}
    for sc in all_candidates:
        key = (sc.chunk.source_id, sc.chunk.chunk_index)
        candidate_index[key] = sc.chunk
    
    for sc in top_chunks:
        chunk = sc.chunk
        source_id = chunk.source_id
        chunk_index = chunk.chunk_index
        
        # Get previous neighbor
        prev_key = (source_id, chunk_index - 1)
        if prev_key in candidate_index and prev_key[1] not in seen_ids:
            neighbor = candidate_index[prev_key]
            if neighbor.id not in seen_ids:
                result_chunks.append(neighbor)
                seen_ids.add(neighbor.id)
        
        # Add main chunk
        if chunk.id not in seen_ids:
            result_chunks.append(chunk)
            seen_ids.add(chunk.id)
        
        # Get next neighbor
        next_key = (source_id, chunk_index + 1)
        if next_key in candidate_index and next_key[1] not in seen_ids:
            neighbor = candidate_index[next_key]
            if neighbor.id not in seen_ids:
                result_chunks.append(neighbor)
                seen_ids.add(neighbor.id)
    
    return result_chunks


def hybrid_search_sync(
    query: str,
    source_ids: list[int],
    game_id: int | None = None,
    keyword_limit: int = 30,
    vector_limit: int = 30,
    final_limit: int = 12,
) -> list[RuleChunk]:
    """
    Synchronous version of hybrid search for use in background jobs.
    
    Simpler implementation without async parallelism.
    """
    from app.db.connection import get_sync_connection
    from app.services.embeddings import create_embedding
    
    logger.info(f"Hybrid search (sync): query='{query[:50]}...'")
    
    # Get embedding
    query_embedding = create_embedding(query)
    embedding_str = "[" + ",".join(map(str, query_embedding)) + "]"
    
    with get_sync_connection() as conn:
        with conn.cursor() as cur:
            # Combined query using CTE
            combined_query = """
                WITH kw_hits AS (
                    SELECT 
                        id,
                        ts_rank_cd(tsv, plainto_tsquery('english', %s)) as bm25_score
                    FROM rule_chunks
                    WHERE source_id = ANY(%s)
                    AND tsv @@ plainto_tsquery('english', %s)
                    AND (expires_at IS NULL OR expires_at > NOW())
                    LIMIT %s
                ),
                vec_hits AS (
                    SELECT 
                        id,
                        1 - (embedding <=> %s::vector) as vec_score
                    FROM rule_chunks
                    WHERE source_id = ANY(%s)
                    AND embedding IS NOT NULL
                    AND (expires_at IS NULL OR expires_at > NOW())
                    ORDER BY embedding <=> %s::vector
                    LIMIT %s
                ),
                combined AS (
                    SELECT 
                        COALESCE(kw.id, vec.id) as id,
                        COALESCE(kw.bm25_score, 0) as bm25_score,
                        COALESCE(vec.vec_score, 0) as vec_score
                    FROM kw_hits kw
                    FULL OUTER JOIN vec_hits vec ON kw.id = vec.id
                )
                SELECT 
                    rc.*,
                    c.bm25_score,
                    c.vec_score,
                    (0.4 * c.bm25_score + 0.6 * c.vec_score) as final_score
                FROM combined c
                JOIN rule_chunks rc ON c.id = rc.id
                ORDER BY final_score DESC
                LIMIT %s
            """
            
            cur.execute(combined_query, (
                query,                  # for ts_rank_cd
                source_ids,             # for kw_hits source filter
                query,                  # for tsv @@ query
                keyword_limit,          # kw limit
                embedding_str,          # for vec score
                source_ids,             # for vec_hits source filter
                embedding_str,          # for vec order
                vector_limit,           # vec limit
                final_limit,            # final limit
            ))
            
            rows = cur.fetchall()
            
            return [RuleChunk.model_validate(dict(row)) for row in rows]
