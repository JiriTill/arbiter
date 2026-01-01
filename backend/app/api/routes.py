"""
API Route Handlers for The Arbiter.
"""

import logging
import time
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import httpx
import redis.asyncio as redis

from app import __version__
from app.config import Settings, get_settings
from app.db import (
    get_db,
    get_games_repo,
    get_sources_repo,
    get_chunks_repo,
    get_history_repo,
    get_feedback_repo,
    get_costs_repo,
    GamesRepository,
    SourcesRepository,
    ChunksRepository,
    HistoryRepository,
    FeedbackRepository,
    CostsRepository,
)
from app.db.models import (
    AskHistoryCreate, 
    Citation, 
    AnswerFeedbackCreate, 
    ApiCostCreate, 
    SourceSuggestionCreate
)
from app.api.schemas import (
    AskRequest,
    AskResponse,
    AskErrorResponse,
    CitationResponse,
    GameResponse,
    GamesListResponse,
    FeedbackRequest,
    FeedbackResponse,
    SourceSuggestionRequest,
    SourceSuggestionResponse,
)
from app.services.answer_generator import generate_answer_with_verification, estimate_answer_quality
from app.services.cache import generate_cache_key, get_cached_answer, cache_answer
from app.services.cost_calculator import calculate_cost
from app.middleware import check_ask_rate_limit, check_ingest_rate_limit, RateLimitResult
from app.middleware.budget import check_budget


logger = logging.getLogger(__name__)
router = APIRouter()


# ============================================================================
# Response Models (System)
# ============================================================================

class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    environment: str
    version: str
    timestamp: str


class ErrorResponse(BaseModel):
    """Standard error response."""
    error: str
    detail: str | None = None


# ============================================================================
# Health & Status Endpoints
# ============================================================================

@router.get(
    "/health",
    response_model=HealthResponse,
    tags=["System"],
    summary="Health check endpoint",
)
async def health_check(settings: Settings = Depends(get_settings)) -> HealthResponse:
    """
    Health check endpoint for monitoring and load balancers.
    
    Returns:
        HealthResponse with status, environment, version, and timestamp.
    """
    return HealthResponse(
        status="ok",
        environment=settings.environment,
        version=__version__,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


@router.get(
    "/",
    tags=["System"],
    summary="API root",
)
async def root():
    """API root endpoint with basic info."""
    return {
        "name": "The Arbiter API",
        "description": "Board game rules Q&A with RAG and citation verification",
        "version": __version__,
        "docs": "/docs",
    }


@router.get(
    "/debug/db",
    tags=["System"],
    summary="Debug database connection",
)
async def debug_db(games_repo: GamesRepository = Depends(get_games_repo)):
    """Debug database connection by listing games."""
    try:
        games = await games_repo.list_games(limit=10)
        return {
            "success": True, 
            "count": len(games),
            "database_connection": "ok",
            "games": [{"id": g.id, "name": g.name} for g in games]
        }
    except Exception as e:
        return {
            "success": False, 
            "database_connection": "failed",
            "error": str(e)
        }


# ============================================================================
# Ask Endpoint (Core Q&A)
# ============================================================================

@router.post(
    "/ask",
    response_model=AskResponse,
    responses={
        200: {"model": AskResponse, "description": "Answer generated successfully"},
        202: {"description": "Indexing in progress"},
        400: {"model": AskErrorResponse, "description": "Bad request"},
        404: {"model": AskErrorResponse, "description": "Game not found"},
        429: {"description": "Rate limit exceeded"},
    },
    tags=["Q&A"],
    summary="Ask a rules question",
)
async def ask_question(
    request: AskRequest,
    rate_limit_result: RateLimitResult = Depends(check_ask_rate_limit),
    games_repo: GamesRepository = Depends(get_games_repo),
    sources_repo: SourcesRepository = Depends(get_sources_repo),
    chunks_repo: ChunksRepository = Depends(get_chunks_repo),
    history_repo: HistoryRepository = Depends(get_history_repo),
    costs_repo: CostsRepository = Depends(get_costs_repo),
    _budget: None = Depends(check_budget),
):
    """
    Ask a rules question about a board game.
    
    This endpoint:
    1. Validates the game exists
    2. Checks if rules are indexed
    3. If not indexed: returns 202 and triggers ingestion
    4. If indexed: generates answer and returns 200
    """
    start_time = time.time()
    
    # 0. Check Answer Cache (Redis)
    cache_key = generate_cache_key(request.game_id, request.edition, request.expansion_ids, request.question)
    try:
        cached_response = await get_cached_answer(cache_key)
        if cached_response:
            # Log cache hit
            try:
                await costs_repo.log_cost(ApiCostCreate(
                    request_id=str(uuid.uuid4()),
                    endpoint="/ask",
                    model="cache",
                    input_tokens=0,
                    output_tokens=0,
                    cost_usd=0.0,
                    cache_hit=True
                ))
            except Exception as e:
                logger.warning(f"Failed to log cache hit: {e}")

            # Add cached flag (not stored in JSON but added on return)
            # We assume stored JSON matches AskResponse structure
            cached_response["cached"] = True
            cached_response["response_time_ms"] = int((time.time() - start_time) * 1000)
            return cached_response
    except Exception as e:
        logger.warning(f"Cache check failed: {e}")
    
    # 1. Get the game
    game = await games_repo.get_game(request.game_id)
    if not game:
        raise HTTPException(
            status_code=404,
            detail={
                "success": False,
                "error": "Game not found",
                "error_code": "GAME_NOT_FOUND",
                "detail": f"No game found with ID {request.game_id}",
            },
        )
    
    # 2. Get sources for this game to find source IDs
    game_with_sources = await games_repo.get_game_with_sources(request.game_id)
    
    if not game_with_sources or not game_with_sources.sources:
        raise HTTPException(
            status_code=404,
            detail={
                "success": False,
                "error": "No sources configured",
                "error_code": "NO_SOURCES",
                "detail": f"No rule sources found for {game.name}. Please add sources first.",
            },
        )
    
    # Filter sources by edition if specified
    source_ids = []
    for source in game_with_sources.sources:
        if request.edition is None or source.edition == request.edition:
            source_ids.append(source.id)
    
    if not source_ids:
        raise HTTPException(
            status_code=404,
            detail={
                "success": False,
                "error": "Edition not found",
                "error_code": "EDITION_NOT_FOUND",
                "detail": f"No sources found for edition '{request.edition}'",
            },
        )
    
    # 3. Check if sources are indexed (have valid, non-expired chunks)
    are_indexed = await sources_repo.sources_are_indexed(source_ids)
    
    if not are_indexed:
        # Get list of unindexed sources
        unindexed_ids = await sources_repo.get_unindexed_source_ids(source_ids)
        
        # Trigger ingestion for unindexed sources
        from app.jobs import enqueue_batch_ingestion
        
        try:
            job_ids = enqueue_batch_ingestion(unindexed_ids)
            primary_job_id = job_ids[0] if job_ids else None
        except Exception as e:
            logger.error(f"Failed to enqueue ingestion: {e}")
            raise HTTPException(
                status_code=500,
                detail={
                    "success": False,
                    "error": "Failed to start indexing",
                    "error_code": "INGESTION_ERROR",
                    "detail": str(e),
                },
            )
        
        # Return 202 Accepted with job info
        return JSONResponse(
            status_code=202,
            content={
                "status": "indexing",
                "job_id": primary_job_id,
                "job_ids": job_ids,
                "status_url": f"/ingest/{primary_job_id}/events" if primary_job_id else None,
                "sources_to_index": len(unindexed_ids),
                "estimated_seconds": 45 * len(unindexed_ids),
                "message": f"Indexing official rules for {game.name}. This happens once per game.",
                "game_name": game.name,
                "edition": request.edition,
                "question": request.question,
            },
        )
    
    # 4. Hybrid search for relevant chunks (keyword + vector)
    try:
        from app.services.retrieval import hybrid_search
        
        chunks, conflict_info = await hybrid_search(
            query=request.question,
            source_ids=source_ids,
            chunks_repo=chunks_repo,
            game_id=request.game_id,
            expansion_ids=request.expansion_ids,
            final_limit=12,
            expand_top_k=5,
            detect_conflicts=True,
        )
    except Exception as e:
        logger.error(f"Hybrid search failed: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": "Search failed",
                "error_code": "SEARCH_ERROR",
                "detail": str(e),
            },
        )
    
    # 5. Generate answer with verification
    try:
        # Pass conflict info to answer generator if present
        conflict_note = None
        if conflict_info:
            from app.services.conflict_detector import generate_conflict_note
            conflict_note = generate_conflict_note(conflict_info)
            logger.info(f"Conflict detected: {conflict_note}")
        
        answer_result = generate_answer_with_verification(
            question=request.question,
            chunks=chunks,
            game_name=game.name,
            edition=request.edition,
            conflict_note=conflict_note,
        )
        
        # Log verification failures
        if not answer_result.get("verified_quote", False):
            logger.warning(
                f"Citation verification failed for game={game.id}, "
                f"question='{request.question[:50]}...'"
            )
    except Exception as e:
        logger.error(f"Answer generation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": "Answer generation failed",
                "error_code": "GENERATION_ERROR",
                "detail": str(e),
            },
        )
    
    # 6. Build response
    confidence, confidence_reason = estimate_answer_quality(answer_result, chunks)
    
    # Only include verified citations
    citations = []
    is_verified = answer_result.get("verified_quote", False)
    quote_chunk_id = answer_result.get("quote_chunk_id")
    
    if is_verified and quote_chunk_id and answer_result.get("quote_exact"):
        # Find the chunk object to get source_id
        chunk_obj = next((c for c in chunks if getattr(c, 'id', 0) == quote_chunk_id), None)
        source_id = getattr(chunk_obj, 'source_id', None) if chunk_obj else None

        citations.append(CitationResponse(
            chunk_id=quote_chunk_id,
            quote=answer_result["quote_exact"],
            page=answer_result.get("page") or 0,
            source_type=answer_result.get("source_type", "rulebook"),
            verified=True,
            source_id=source_id,
        ))
    
    # 7. Check for superseded rule (when using expansion that overrides base)
    superseded_rule = None
    if quote_chunk_id:
        try:
            # Look up the chunk to check for override
            cited_chunk = await chunks_repo.get_by_id(quote_chunk_id)
            if cited_chunk and cited_chunk.overrides_chunk_id:
                # Fetch the overridden base chunk
                base_chunk = await chunks_repo.get_by_id(cited_chunk.overrides_chunk_id)
                if base_chunk:
                    # Get expansion name for reason
                    expansion_name = getattr(cited_chunk, 'expansion_name', None)
                    if not expansion_name:
                        # Try to get from expansion_id
                        from app.db.repositories.expansions import get_expansions_repo
                        exp_repo = await get_expansions_repo()
                        if cited_chunk.expansion_id:
                            expansion = await exp_repo.get_by_id(cited_chunk.expansion_id)
                            expansion_name = expansion.name if expansion else "Expansion"
                        else:
                            expansion_name = "Expansion"
                    
                    superseded_rule = {
                        "quote": base_chunk.chunk_text[:300],
                        "page": base_chunk.page_number,
                        "source_type": "rulebook",
                        "reason": f"{expansion_name} supersedes this base rule",
                        "confidence": cited_chunk.override_confidence or 0,
                    }
                    logger.info(f"Found superseded rule: base chunk {base_chunk.id}")
        except Exception as e:
            logger.warning(f"Failed to fetch superseded rule: {e}")
    
    response_time_ms = int((time.time() - start_time) * 1000)
    
    # 8. Save to history
    history_id = None
    try:
        # Normalize question for caching
        normalized_q = request.question.lower().strip()
        
        # Get embedding from cache (was created during hybrid search)
        from app.services.cache import get_cached_embedding
        question_embedding = get_cached_embedding(request.question) or []
        
        history_create = AskHistoryCreate(
            game_id=request.game_id,
            edition=request.edition,
            expansions_used=request.expansion_ids,
            question=request.question,
            normalized_question=normalized_q,
            question_embedding=question_embedding,
            verdict=answer_result.get("verdict", ""),
            confidence=confidence,
            confidence_reason=confidence_reason,
            citations=[
                Citation(
                    chunk_id=c.chunk_id,
                    quote=c.quote,
                    page=c.page,
                    verified=c.verified,
                )
                for c in citations
            ],
            response_time_ms=response_time_ms,
            model_used="gpt-4o-mini",
        )
        
        saved_history = await history_repo.save_query(history_create)
        history_id = saved_history.id
    except Exception as e:
        logger.warning(f"Failed to save to history: {e}")
        # Don't fail the request if history save fails
    
    # Build response dict (to include optional superseded_rule)
    response_data = {
        "success": True,
        "verdict": answer_result.get("verdict", "Unable to determine"),
        "confidence": confidence,
        "confidence_reason": confidence_reason,
        "citations": citations,
        "game_name": game.name,
        "edition": request.edition,
        "question": request.question,
        "history_id": history_id,
        "response_time_ms": response_time_ms,
    }
    
    if superseded_rule:
        response_data["superseded_rule"] = superseded_rule
    
    if answer_result.get("conflict_note"):
        response_data["conflict_note"] = answer_result["conflict_note"]
    
    if answer_result.get("notes"):
        response_data["notes"] = answer_result["notes"]
    
    # 5. Cache verified answers (Redis)
    if answer_result.get("verified_quote"):
        try:
            await cache_answer(cache_key, response_data)
        except Exception as e:
            logger.warning(f"Failed to cache answer: {e}")
    
    # 6. Log cost
    usage = answer_result.get("_usage")
    if usage:
        try:
            cost_usd = calculate_cost(usage["model"], usage["input_tokens"], usage["output_tokens"])
            await costs_repo.log_cost(ApiCostCreate(
                request_id=str(uuid.uuid4()),
                endpoint="/ask",
                model=usage["model"],
                input_tokens=usage["input_tokens"],
                output_tokens=usage["output_tokens"],
                cost_usd=cost_usd,
                cache_hit=False
            ))
        except Exception as e:
            logger.warning(f"Failed to log cost: {e}")

    return response_data


# ============================================================================
# Games Endpoints
# ============================================================================

@router.get(
    "/games",
    response_model=GamesListResponse,
    tags=["Games"],
    summary="List available games",
)
async def list_games(
    search: str | None = None,
    limit: int = 50,
    offset: int = 0,
    games_repo: GamesRepository = Depends(get_games_repo),
):
    """List all available games, optionally filtered by search term."""
    games = await games_repo.list_games_with_sources(limit=limit, offset=offset, search=search)
    
    response_games = []
    for game in games:
        editions = sorted(list(set(s.edition for s in game.sources)))
        
        response_games.append(GameResponse(
            id=game.id,
            name=game.name,
            slug=game.slug,
            bgg_id=game.bgg_id,
            cover_image_url=game.cover_image_url,
            editions=editions,
            has_indexed_sources=len(game.sources) > 0,
            sources=[
                {
                    "id": s.id,
                    "source_type": s.source_type,
                    "edition": s.edition,
                    "needs_ocr": s.needs_ocr,
                    "expansion_id": s.expansion_id,
                }
                for s in game.sources
            ],
        ))
    
    return GamesListResponse(
        games=response_games,
        total=len(response_games),
    )


@router.get(
    "/games/{game_id}",
    response_model=GameResponse,
    tags=["Games"],
    summary="Get game details",
)
async def get_game(
    game_id: int,
    games_repo: GamesRepository = Depends(get_games_repo),
):
    """Get details for a specific game."""
    game = await games_repo.get_game_with_sources(game_id)
    
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    
    # Extract unique editions from sources
    editions = list({s.edition for s in game.sources})
    
    return GameResponse(
        id=game.id,
        name=game.name,
        slug=game.slug,
        bgg_id=game.bgg_id,
        cover_image_url=game.cover_image_url,
        editions=editions,
        has_indexed_sources=len(game.sources) > 0,
        sources=[
            {
                "id": s.id,
                "source_type": s.source_type,
                "edition": s.edition,
                "needs_ocr": s.needs_ocr,
                "expansion_id": s.expansion_id,
            }
            for s in game.sources
        ],
    )


@router.get(
    "/games/{game_id}/expansions",
    tags=["Games"],
    summary="Get game expansions",
)
async def get_game_expansions(game_id: int):
    """Get all expansions for a game."""
    from app.db.repositories.expansions import get_expansions_repo
    
    expansions_repo = await get_expansions_repo()
    expansions = await expansions_repo.get_by_game_id(game_id)
    
    return {
        "success": True,
        "game_id": game_id,
        "expansions": [
            {
                "id": e.id,
                "name": e.name,
                "code": e.code,
                "description": e.description,
                "releaseDate": e.release_date.isoformat() if e.release_date else None,
                "displayOrder": e.display_order,
            }
            for e in expansions
        ],
        "count": len(expansions),
    }



# ============================================================================
# Feedback Endpoints
# ============================================================================

@router.post(
    "/feedback",
    response_model=FeedbackResponse,
    tags=["Feedback"],
    summary="Submit feedback on an answer",
)
async def submit_feedback(
    request: FeedbackRequest,
    feedback_repo: FeedbackRepository = Depends(get_feedback_repo),
):
    """
    Submit user feedback for an answer in history.
    """
    try:
        feedback = AnswerFeedbackCreate(
            ask_history_id=request.ask_history_id,
            feedback_type=request.feedback_type,
            selected_chunk_id=request.selected_chunk_id,
            user_note=request.user_note,
        )
        saved = await feedback_repo.save_feedback(feedback)
        return FeedbackResponse(success=True, feedback_id=saved.id)
    except Exception as e:
        logger.error(f"Failed to save feedback: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Source Endpoints
# ============================================================================

@router.post(
    "/sources/suggest",
    response_model=SourceSuggestionResponse,
    summary="Suggest a better source",
    tags=["Sources"],
)
async def suggest_source(
    suggestion: SourceSuggestionRequest,
    sources_repo: SourcesRepository = Depends(get_sources_repo),
):
    """Submit a suggestion for a better game source."""
    result = await sources_repo.create_suggestion(SourceSuggestionCreate(
        game_id=suggestion.game_id,
        suggested_url=suggestion.suggested_url,
        user_note=suggestion.user_note
    ))
    
    return SourceSuggestionResponse(
        success=True,
        suggestion_id=result.id,
        status=result.status
    )


# ============================================================================
# Ingestion Endpoints
# ============================================================================

class IngestRequest(BaseModel):
    """Request to start ingestion."""
    source_id: int
    force: bool = False


class IngestResponse(BaseModel):
    """Response from ingestion trigger."""
    job_id: str
    source_id: int
    status_url: str
    events_url: str
    estimated_seconds: int


class IngestStatusResponse(BaseModel):
    """Job status response."""
    job_id: str
    state: str
    pct: int
    message: str
    result: dict | None = None
    error: str | None = None


@router.post(
    "/ingest",
    response_model=IngestResponse,
    tags=["Ingestion"],
    summary="Start source ingestion",
    responses={
        429: {"description": "Rate limit exceeded"},
    },
)
async def start_ingestion(
    request: IngestRequest,
    rate_limit_result: RateLimitResult = Depends(check_ingest_rate_limit),
):
    """
    Start ingesting a source document.
    
    This enqueues a background job that:
    1. Downloads the PDF
    2. Extracts text
    3. Chunks the content
    4. Generates embeddings
    5. Saves to database
    
    Returns a job_id that can be used to track progress via SSE.
    """
    from app.jobs import enqueue_ingestion
    
    try:
        job_id = enqueue_ingestion(request.source_id, request.force)
    except Exception as e:
        logger.error(f"Failed to enqueue ingestion: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to enqueue job: {e}"
        )
    
    return IngestResponse(
        job_id=job_id,
        source_id=request.source_id,
        status_url=f"/ingest/{job_id}/status",
        events_url=f"/ingest/{job_id}/events",
        estimated_seconds=60,  # Rough estimate
    )


@router.get(
    "/ingest/{job_id}/status",
    response_model=IngestStatusResponse,
    tags=["Ingestion"],
    summary="Get ingestion job status",
)
async def get_ingestion_status(job_id: str):
    """Get current status of an ingestion job."""
    from app.jobs import get_job_status
    
    status = get_job_status(job_id)
    
    return IngestStatusResponse(
        job_id=job_id,
        state=status.get("state", "unknown"),
        pct=status.get("pct", 0),
        message=status.get("message", ""),
        result=status.get("result"),
        error=status.get("error"),
    )


@router.get(
    "/ingest/{job_id}/events",
    tags=["Ingestion"],
    summary="Stream ingestion progress (SSE)",
    response_description="Server-Sent Events stream",
)
async def stream_ingestion_events(job_id: str):
    """
    Stream ingestion progress updates via Server-Sent Events.
    
    Events are sent as:
    ```
    event: progress
    data: {"state":"downloading","pct":15,"msg":"Fetching PDF..."}
    
    event: complete
    data: {"state":"ready","pct":100,"msg":"Done"}
    ```
    
    The stream ends when state is 'ready' or 'failed'.
    """
    from app.jobs import get_job_status
    from app.api.sse import SSEResponse, sse_generator
    
    async def poll_job_status():
        """Poll Redis for job status."""
        status = get_job_status(job_id)
        return {
            "state": status.get("state", "unknown"),
            "pct": status.get("pct", 0),
            "msg": status.get("message", ""),
            "result": status.get("result"),
            "error": status.get("error"),
        }
    
    return SSEResponse(
        sse_generator(
            poll_func=poll_job_status,
            poll_interval=0.5,
            timeout=300,
            terminal_states={"ready", "failed", "error", "unknown"},
        )
    )


@router.get(
    "/ingest/queue/stats",
    tags=["Ingestion"],
    summary="Get queue statistics",
)
async def get_queue_statistics():
    """Get statistics about the ingestion queue."""
    from app.jobs import get_queue_stats
    
    try:
        stats = get_queue_stats()
        return {
            "success": True,
            **stats,
        }
    except Exception as e:
        logger.error(f"Failed to get queue stats: {e}")
        return {
            "success": False,
            "error": str(e),
        }


# ============================================================================
# Admin Endpoints
# ============================================================================

class CleanupResponse(BaseModel):
    """Response from cleanup operation."""
    success: bool
    deleted_chunks: int
    affected_sources: int
    source_ids: list[int]
    duration_ms: int
    error: str | None = None


@router.post(
    "/admin/cleanup",
    response_model=CleanupResponse,
    tags=["Admin"],
    summary="Trigger cleanup of expired chunks",
)
async def trigger_cleanup():
    """
    Manually trigger cleanup of expired chunks.
    
    This will:
    1. Delete all chunks where expires_at < now()
    2. Mark affected sources as needs_reingest = true
    
    Use this for testing or immediate cleanup needs.
    Production should rely on the scheduled job.
    """
    from app.jobs import cleanup_expired_chunks
    
    try:
        result = cleanup_expired_chunks()
        
        return CleanupResponse(
            success="error" not in result,
            deleted_chunks=result.get("deleted_chunks", 0),
            affected_sources=result.get("affected_sources", 0),
            source_ids=result.get("source_ids", []),
            duration_ms=result.get("duration_ms", 0),
            error=result.get("error"),
        )
    except Exception as e:
        logger.error(f"Cleanup failed: {e}")
        return CleanupResponse(
            success=False,
            deleted_chunks=0,
            affected_sources=0,
            source_ids=[],
            duration_ms=0,
            error=str(e),
        )


@router.post(
    "/admin/cleanup/all",
    tags=["Admin"],
    summary="Run all cleanup jobs",
)
async def trigger_full_cleanup():
    """
    Run all cleanup jobs including history and violations.
    
    Jobs run:
    - cleanup_expired_chunks
    - cleanup_old_history (90 days retention)
    - cleanup_rate_limit_violations (30 days retention)
    """
    from app.jobs import run_all_cleanup_jobs
    
    try:
        result = run_all_cleanup_jobs()
        return {
            "success": True,
            **result,
        }
    except Exception as e:
        logger.error(f"Full cleanup failed: {e}")
        return {
            "success": False,
            "error": str(e),
        }


@router.get(
    "/admin/scheduled-jobs",
    tags=["Admin"],
    summary="List scheduled jobs",
)
async def list_scheduled_jobs():
    """List all scheduled background jobs."""
    try:
        from app.jobs.scheduler import list_scheduled_jobs
        jobs = list_scheduled_jobs()
        return {
            "success": True,
            "jobs": jobs,
            "count": len(jobs),
        }
    except Exception as e:
        logger.error(f"Failed to list scheduled jobs: {e}")
        return {
            "success": False,
            "error": str(e),
        }


@router.get(
    "/admin/source-health",
    tags=["Admin"],
    summary="Get source health status",
)
async def get_source_health(
    status_filter: str | None = None,
    problems_only: bool = False,
):
    """
    Get health status of all game sources.
    
    Query params:
    - status_filter: Filter by status (ok, changed, unreachable, error)
    - problems_only: If true, only show sources with problems
    """
    from app.jobs import get_health_summary
    
    try:
        summary = get_health_summary()
        
        sources = summary.get("sources", [])
        
        # Apply filters
        if problems_only:
            sources = [s for s in sources if s.get("status") != "ok"]
        elif status_filter:
            sources = [s for s in sources if s.get("status") == status_filter]
        
        return {
            "success": True,
            "total": summary.get("total", 0),
            "status_counts": summary.get("status_counts", {}),
            "sources": sources,
        }
    except Exception as e:
        logger.error(f"Failed to get source health: {e}")
        return {
            "success": False,
            "error": str(e),
        }


@router.post(
    "/admin/source-health/check",
    tags=["Admin"],
    summary="Trigger source health check",
)
async def trigger_source_health_check(source_id: int | None = None):
    """
    Trigger health check for sources.
    
    If source_id is provided, checks only that source.
    Otherwise checks all sources.
    """
    from app.jobs import check_source_health, check_all_sources
    
    try:
        if source_id is not None:
            result = check_source_health(source_id)
            return {
                "success": True,
                "result": result,
            }
        else:
            result = check_all_sources()
            return {
                "success": True,
                **result,
            }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "success": False,
            "error": str(e),
        }


@router.get(
    "/admin/source-health/history/{source_id}",
    tags=["Admin"],
    summary="Get health check history for a source",
)
async def get_source_health_history(source_id: int, limit: int = 30):
    """Get historical health checks for a specific source."""
    from app.db.connection import get_async_pool
    
    try:
        pool = await get_async_pool()
        async with pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute("""
                    SELECT 
                        id,
                        status,
                        http_code,
                        file_hash,
                        content_length,
                        error,
                        last_checked_at
                    FROM source_health
                    WHERE source_id = %s
                    ORDER BY last_checked_at DESC
                    LIMIT %s
                """, (source_id, limit))
                
                rows = await cur.fetchall()
                
                history = [
                    {
                        "id": row["id"],
                        "status": row["status"],
                        "http_code": row["http_code"],
                        "file_hash": row["file_hash"][:8] + "..." if row["file_hash"] else None,
                        "content_length": row["content_length"],
                        "error": row["error"],
                        "checked_at": row["last_checked_at"].isoformat(),
                    }
                    for row in rows
                ]
                
                return {
                    "success": True,
                    "source_id": source_id,
                    "history": history,
                    "count": len(history),
                }
    except Exception as e:
        logger.error(f"Failed to get health history: {e}")
        return {
            "success": False,
            "error": str(e),
        }


@router.get("/sources/{source_id}/pdf")
async def get_source_pdf(
    source_id: int,
    sources_repo: SourcesRepository = Depends(get_sources_repo),
    settings: Settings = Depends(get_settings),
):
    """Proxy PDF content for in-app viewing."""
    source = await sources_repo.get_source(source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    
    if not source.source_url:
        raise HTTPException(status_code=400, detail="Source has no URL")

    # Cache key
    cache_key = f"pdf:{source_id}"
    
    # Check cache
    try:
        # Check settings
        if getattr(settings, "redis_url", None):
            client = redis.from_url(settings.redis_url, decode_responses=False)
            async with client:
                cached_data = await client.get(cache_key)
                if cached_data:
                    return Response(
                        content=cached_data, 
                        media_type="application/pdf",
                        headers={"Content-Disposition": f'inline; filename="source_{source_id}.pdf"'}
                    )
    except Exception as e:
        logger.error(f"Redis cache error: {e}")

    # Fetch
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(source.source_url, timeout=30.0, follow_redirects=True)
            if resp.status_code != 200:
                raise HTTPException(status_code=502, detail="Failed to fetch PDF from upstream")
            
            content = resp.content
            
            # Cache it
            try:
                if getattr(settings, "redis_url", None):
                    redis_client = redis.from_url(settings.redis_url, decode_responses=False)
                    async with redis_client:
                        await redis_client.set(cache_key, content, ex=3600) # 1 hour
            except Exception as e:
                logger.error(f"Redis set error: {e}")
                
            return Response(
                content=content,
                media_type="application/pdf",
                headers={"Content-Disposition": f'inline; filename="source_{source_id}.pdf"'}
            )
        except httpx.RequestError as e:
            raise HTTPException(status_code=502, detail=f"Failed to fetch PDF: {str(e)}")

