"""
Admin API endpoints for content management and analytics.
"""

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from supabase import create_client, Client

from app.config import get_settings
from app.db import (
    get_feedback_repo,
    get_costs_repo,
    get_games_repo,
    get_sources_repo,
    FeedbackRepository,
    CostsRepository,
    GamesRepository,
    SourcesRepository,
)
from app.db.models import GameCreate, GameSourceCreate


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin", tags=["Admin"])

# Storage bucket name for rulebooks
STORAGE_BUCKET = "rulebooks"


def get_supabase_client() -> Client:
    """Get Supabase client for storage operations."""
    settings = get_settings()
    return create_client(settings.supabase_url, settings.supabase_service_role_key)


# =============================================================================
# Games Management
# =============================================================================

@router.get("/games")
async def list_games(
    limit: int = 50,
    offset: int = 0,
    search: str | None = None,
    games_repo: GamesRepository = Depends(get_games_repo),
) -> list[dict[str, Any]]:
    """List all games with their sources."""
    games = await games_repo.list_games_with_sources(limit=limit, offset=offset, search=search)
    return [g.model_dump() for g in games]


@router.post("/games")
async def create_game(
    name: str = Form(...),
    slug: str = Form(...),
    bgg_id: int | None = Form(None),
    cover_image_url: str | None = Form(None),
    games_repo: GamesRepository = Depends(get_games_repo),
) -> dict[str, Any]:
    """Create a new game."""
    game_data = GameCreate(
        name=name,
        slug=slug,
        bgg_id=bgg_id,
        cover_image_url=cover_image_url,
    )
    game = await games_repo.create_game(game_data)
    return {"success": True, "game": game.model_dump()}


@router.put("/games/{game_id}")
async def update_game(
    game_id: int,
    name: str = Form(...),
    slug: str = Form(...),
    bgg_id: int | None = Form(None),
    cover_image_url: str | None = Form(None),
    games_repo: GamesRepository = Depends(get_games_repo),
) -> dict[str, Any]:
    """Update an existing game."""
    game_data = GameCreate(
        name=name,
        slug=slug,
        bgg_id=bgg_id,
        cover_image_url=cover_image_url,
    )
    game = await games_repo.update_game(game_id, game_data)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    return {"success": True, "game": game.model_dump()}


@router.get("/games/{game_id}")
async def get_game(
    game_id: int,
    games_repo: GamesRepository = Depends(get_games_repo),
) -> dict[str, Any]:
    """Get a single game with all sources."""
    game = await games_repo.get_game_with_sources(game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    return game.model_dump()


# =============================================================================
# Sources Management
# =============================================================================

@router.get("/sources")
async def list_sources(
    game_id: int | None = None,
    source_type: str | None = None,
    limit: int = 50,
    offset: int = 0,
    sources_repo: SourcesRepository = Depends(get_sources_repo),
) -> list[dict[str, Any]]:
    """List all sources with optional filters."""
    sources = await sources_repo.list_sources(
        game_id=game_id,
        source_type=source_type,
        limit=limit,
        offset=offset,
    )
    return [s.model_dump() for s in sources]


@router.post("/sources")
async def create_source(
    game_id: int = Form(...),
    edition: str = Form(...),
    source_type: str = Form("rulebook"),
    source_url: str = Form(...),
    is_official: bool = Form(True),
    needs_ocr: bool = Form(False),
    sources_repo: SourcesRepository = Depends(get_sources_repo),
) -> dict[str, Any]:
    """Create a new source (with URL)."""
    source_data = GameSourceCreate(
        game_id=game_id,
        edition=edition,
        source_type=source_type,
        source_url=source_url,
        is_official=is_official,
        needs_ocr=needs_ocr,
    )
    source = await sources_repo.create_source(source_data)
    return {"success": True, "source": source.model_dump()}


@router.post("/sources/upload")
async def upload_source_pdf(
    game_id: int = Form(...),
    edition: str = Form(...),
    source_type: str = Form("rulebook"),
    is_official: bool = Form(True),
    needs_ocr: bool = Form(False),
    file: UploadFile = File(...),
    sources_repo: SourcesRepository = Depends(get_sources_repo),
    games_repo: GamesRepository = Depends(get_games_repo),
) -> dict[str, Any]:
    """
    Upload a PDF rulebook to Supabase Storage and create source entry.
    
    This endpoint:
    1. Validates the file is a PDF
    2. Uploads to Supabase Storage
    3. Creates a source entry with the storage URL
    """
    # Validate file type
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="File must be a PDF")
    
    # Get game to use slug for filename
    game = await games_repo.get_game(game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    
    # Generate storage path: rulebooks/{game_slug}/{edition}_{source_type}.pdf
    safe_edition = edition.lower().replace(" ", "-").replace("/", "-")
    filename = f"{safe_edition}_{source_type}.pdf"
    storage_path = f"{game.slug}/{filename}"
    
    try:
        # Read file content
        file_content = await file.read()
        
        # Upload to Supabase Storage
        supabase = get_supabase_client()
        settings = get_settings()
        
        # Upload file
        result = supabase.storage.from_(STORAGE_BUCKET).upload(
            path=storage_path,
            file=file_content,
            file_options={"content-type": "application/pdf", "upsert": "true"}
        )
        
        # Get public URL
        public_url = f"{settings.supabase_url}/storage/v1/object/public/{STORAGE_BUCKET}/{storage_path}"
        
        logger.info(f"Uploaded PDF to: {public_url}")
        
        # Create source entry
        source_data = GameSourceCreate(
            game_id=game_id,
            edition=edition,
            source_type=source_type,
            source_url=public_url,
            is_official=is_official,
            needs_ocr=needs_ocr,
        )
        source = await sources_repo.create_source(source_data)
        
        return {
            "success": True,
            "source": source.model_dump(),
            "storage_path": storage_path,
            "public_url": public_url,
            "file_size_mb": round(len(file_content) / (1024 * 1024), 2),
        }
        
    except Exception as e:
        logger.error(f"Failed to upload PDF: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.post("/sources/{source_id}/reingest")
async def trigger_reingest(
    source_id: int,
    sources_repo: SourcesRepository = Depends(get_sources_repo),
) -> dict[str, Any]:
    """Mark a source for re-ingestion."""
    await sources_repo.mark_needs_reingest(source_id)
    return {"success": True, "message": f"Source {source_id} marked for re-ingestion"}


# =============================================================================
# Feedback & Costs (existing)
# =============================================================================

@router.get("/feedback")
async def get_feedback(
    type: str | None = None,
    limit: int = 20,
    offset: int = 0,
    feedback_repo: FeedbackRepository = Depends(get_feedback_repo),
) -> list[dict[str, Any]]:
    """Get recent user feedback with search/filter options."""
    return await feedback_repo.get_recent_feedback(
        feedback_type=type,
        limit=limit,
        offset=offset,
    )


@router.get("/costs")
async def get_costs(
    period: str = "today",
    costs_repo: CostsRepository = Depends(get_costs_repo)
):
    """Get API cost statistics. Period can be 'today', 'week', 'month'."""
    return await costs_repo.get_stats(period)

