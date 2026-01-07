"""
Admin API endpoints for content management and analytics.
"""

import logging
from typing import Any
import shutil
import os
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Request, Body
from supabase import create_client, Client

from app.config import get_settings
from app.db import (
    get_feedback_repo,
    get_costs_repo,
    get_games_repo,
    get_sources_repo,
    get_chunks_repo,
    FeedbackRepository,
    CostsRepository,
    GamesRepository,
    SourcesRepository,
    ChunksRepository,
)
from app.db.models import GameCreate, GameSourceCreate


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin", tags=["Admin"])

# Storage bucket name for rulebooks
STORAGE_BUCKET = "Rulebooks"


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


@router.post("/sources/{source_id}/process")
async def start_processing(
    source_id: int,
    force: bool = False,
    sources_repo: SourcesRepository = Depends(get_sources_repo),
) -> dict[str, Any]:
    """
    Immediately start processing a source in the background.
    
    This triggers ingestion (including OCR for scanned PDFs) without
    waiting for a user question. Useful for pre-processing uploaded PDFs.
    """
    from app.jobs import enqueue_ingestion
    
    try:
        # Reset the needs_ocr flag so processing actually happens
        # (otherwise it might skip because it was marked as needing OCR)
        source = await sources_repo.get_source(source_id)
        if not source:
            raise HTTPException(status_code=404, detail="Source not found")
        
        # Clear the needs_ocr flag and mark for reingest
        await sources_repo.mark_needs_reingest(source_id)
        
        # Enqueue the ingestion job
        job_id = enqueue_ingestion(source_id, force=True)
        
        return {
            "success": True,
            "job_id": job_id,
            "source_id": source_id,
            "message": f"Processing started for source {source_id}",
            "status_url": f"/ingest/{job_id}/status",
            "note": "OCR processing may take 10-20 minutes for large scanned PDFs",
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start processing: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start processing: {str(e)}")


@router.get("/sources/{source_id}/status")
async def get_source_status(
    source_id: int,
    sources_repo: SourcesRepository = Depends(get_sources_repo),
) -> dict[str, Any]:
    """Get the processing status of a source."""
    source = await sources_repo.get_source(source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    
    status = "unknown"
    if source.last_ingested_at:
        status = "indexed"
    elif source.needs_ocr:
        status = "needs_ocr"
    elif source.needs_reingest:
        status = "pending"
    else:
        status = "not_started"
    
    return {
        "source_id": source_id,
        "status": status,
        "needs_ocr": source.needs_ocr,
        "needs_reingest": source.needs_reingest,
        "last_ingested_at": source.last_ingested_at.isoformat() if source.last_ingested_at else None,
    }


@router.delete("/sources/{source_id}")
async def delete_source(
    source_id: int,
    request: Request,
    sources_repo: SourcesRepository = Depends(get_sources_repo),
    chunks_repo: ChunksRepository = Depends(get_chunks_repo),
) -> dict[str, Any]:
    """Delete a source and its associated chunks."""
    
    # 1. Check if source exists
    source = await sources_repo.get_source(source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    
    # 2. Delete chunks
    await chunks_repo.delete_chunks_by_source(source_id)
    
    # 3. Delete source
    deleted = await sources_repo.delete_source(source_id)
    
    if not deleted:
        raise HTTPException(status_code=500, detail="Failed to delete source")
        
    return {"success": True, "message": f"Source {source_id} deleted"}


@router.post("/maintenance/fix-images")
async def fix_game_images():
    """Fix broken BGG image URLs by removing filter parameters."""
    count = 0
    from app.db.connection import get_async_connection
    
    debug_info = []
    
    async with get_async_connection() as conn:
        async with conn.cursor() as cur:
            # Broader search: any URL containing /fit-in/
            await cur.execute("SELECT id, name, cover_image_url FROM games WHERE cover_image_url LIKE '%/fit-in/%'")
            rows = await cur.fetchall()
            
            debug_info.append(f"Found {len(rows)} games with /fit-in/ URLs")
            
            for row in rows:
                game_id, name, url = row
                if "/fit-in/" in url and "/pic" in url:
                    try:
                        # Extract base path and filename
                        base_part = url.split("/fit-in/")[0]
                        filename = url.split("/")[-1]
                        new_url = f"{base_part}/{filename}"
                        
                        debug_info.append(f"Fixing {name}: .../{url.split('/')[-1]} -> {new_url.split('/')[-1]}")
                        
                        await cur.execute(
                            "UPDATE games SET cover_image_url = %s WHERE id = %s",
                            (new_url, game_id)
                        )
                        count += 1
                    except Exception as e:
                        debug_info.append(f"Error fixing {name}: {e}")
            
            await conn.commit()
            
    return {
        "success": True, 
        "fixed_count": count, 
        "message": f"Fixed {count} image URLs",
        "debug": debug_info
    }


@router.get("/maintenance/urls")
async def get_image_urls():
    """Get all game image URLs for debugging."""
    from app.db.connection import get_async_connection
    async with get_async_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute("SELECT id, name, cover_image_url FROM games")
            rows = await cur.fetchall()
            return [{"id": r[0], "name": r[1], "url": r[2]} for r in rows]



@router.post("/games/{game_id}/image")
async def upload_game_image(
    game_id: int,
    file: UploadFile = File(...),
    alt_text: str | None = Form(None),
    games_repo: GamesRepository = Depends(get_games_repo),
):
    """Upload a game image to local static storage."""
    
    # 1. Validate File
    if file.content_type not in ["image/jpeg", "image/png", "image/jpg"]:
        raise HTTPException(400, "Only JPEG/PNG Allowed.")
    
    # 2. Get Game
    game = await games_repo.get_game(game_id)
    if not game:
        raise HTTPException(404, "Game not found")

    # 3. Create Directory
    static_images_dir = Path("app/static/images/games")
    static_images_dir.mkdir(parents=True, exist_ok=True)
    
    # 4. Generate Filename
    safe_name = game.slug if game.slug else f"game-{game_id}"
    ext = ".jpg" if "jpeg" in file.content_type or "jpg" in file.content_type else ".png"
    filename = f"{safe_name}{ext}"
    file_path = static_images_dir / filename
    
    # 5. Save File
    try:
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        logger.error(f"Failed to save image: {e}")
        raise HTTPException(500, "Failed to save file")
        
    # 6. Update DB
    from app.db.models import GameCreate
    
    updated_game_data = GameCreate(
        name=game.name,
        slug=game.slug,
        bgg_id=game.bgg_id,
        cover_image_url=None, 
        image_filename=filename,
        image_alt_text=alt_text or f"Cover for {game.name}"
    )
    
    await games_repo.update_game(game_id, updated_game_data)
    
    return {"success": True, "filename": filename}

"""
Legacy BGG Logic:

    import asyncio
    import xml.etree.ElementTree as ET
    from app.db.connection import get_async_connection
    
    results = []
    errors = []
    
    async with get_async_connection() as conn:
        async with conn.cursor() as cur:
            # Get all games with bgg_id
            await cur.execute("SELECT id, name, bgg_id FROM games WHERE bgg_id IS NOT NULL")
            rows = await cur.fetchall()
            
            logger.info(f"Found {len(rows)} games with BGG IDs")
            
            # Semaphore to limit concurrency (BGG rate limits)
            sem = asyncio.Semaphore(2)  # Lower concurrency to avoid blocking

            # Detailed browser headers
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
                "Referer": "https://boardgamegeek.com/",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1"
            }
            
            async with httpx.AsyncClient(timeout=45.0, headers=headers, follow_redirects=True) as client:
                
                async def fetch_bgg(bgg_id, use_v1=False):
                    url = f"https://boardgamegeek.com/xmlapi/boardgame/{bgg_id}" if use_v1 else f"https://boardgamegeek.com/xmlapi2/thing?id={bgg_id}"
                    return await client.get(url)

                async def process_game(row):
                    game_id, name, bgg_id = row[0], row[1], row[2]
                    async with sem:
                        try:
                            # Random delay to look human
                            import random
                            await asyncio.sleep(random.uniform(0.5, 2.0))
                            
                            # Try v2
                            response = await fetch_bgg(bgg_id)
                            
                            # If blocked, try v1
                            if response.status_code in [401, 403, 429]:
                                logger.warning(f"BGG v2 blocked ({response.status_code}) for {name}, trying v1...")
                                await asyncio.sleep(2)
                                response = await fetch_bgg(bgg_id, use_v1=True)
                            
                            if response.status_code != 200:
                                return {"error": f"BGG returned {response.status_code}", "game": name}
                            
                            # Parse XML
                            root = ET.fromstring(response.content)
                            
                            # Log first 100 bytes for debugging if needed
                            # logger.info(f"Response: {response.content[:100]}")
                            
                            image_url = None
                            
                            # v2 structure vs v1 structure
                            # v2: <item><thumbnail>...</thumbnail><image>...</image></item>
                            # v1: <boardgame><thumbnail>...</thumbnail><image>...</image></boardgame>
                            
                            thumbnail_elem = root.find(".//thumbnail")
                            image_elem = root.find(".//image")
                            
                            if thumbnail_elem is not None and thumbnail_elem.text:
                                image_url = thumbnail_elem.text
                            elif image_elem is not None and image_elem.text:
                                image_url = image_elem.text
                            
                            if not image_url:
                                return {"error": "No image found in BGG response", "game": name}
                            
                            # Ensure absolute URL
                            if image_url and not image_url.startswith("http"):
                                image_url = f"https:{image_url}" if image_url.startswith("//") else f"https://boardgamegeek.com{image_url}"
                            
                            return {
                                "success": True,
                                "game_id": game_id,
                                "game": name,
                                "bgg_id": bgg_id,
                                "image_url": image_url
                            }
                            
                        except ET.ParseError as e:
                            return {"error": f"XML parse error: {str(e)}", "game": name}
                        except Exception as e:
                            return {"error": str(e), "game": name}

                # Run all tasks
                tasks = [process_game(row) for row in rows]
                batch_results = await asyncio.gather(*tasks)
                
                # Process results and update DB
                for res in batch_results:
                    if "error" in res:
                        errors.append(res)
                    else:
                        await cur.execute(
                            "UPDATE games SET cover_image_url = %s WHERE id = %s",
                            (res["image_url"], res["game_id"])
                        )
                        results.append({
                            "game": res["game"],
                            "bgg_id": res["bgg_id"],
                            "image_url": res["image_url"][:60] + "..." if len(res["image_url"]) > 60 else res["image_url"]
                        })
                        logger.info(f"Updated {res['game']} with image from BGG")
                
            await conn.commit()
    
    return {
        "success": True,
        "updated": len(results),
        "errors": len(errors),
        "results": results,
        "error_details": errors
    }
"""





@router.get("/maintenance/failed-jobs")
async def get_failed_jobs():
    """Get list of failed jobs with their error messages."""
    from app.jobs.queue import get_queue, get_redis_connection
    from rq.job import Job
    
    queue = get_queue("default")
    failed_registry = queue.failed_job_registry
    
    failed_jobs = []
    for job_id in failed_registry.get_job_ids():
        try:
            job = Job.fetch(job_id, connection=get_redis_connection())
            failed_jobs.append({
                "job_id": job_id,
                "exc_info": str(job.exc_info)[:500] if job.exc_info else None,
                "created_at": str(job.created_at) if job.created_at else None,
                "ended_at": str(job.ended_at) if job.ended_at else None,
                "args": str(job.args) if job.args else None,
            })
        except Exception as e:
            failed_jobs.append({"job_id": job_id, "error": str(e)})
    
    return {
        "failed_count": len(failed_jobs),
        "jobs": failed_jobs[:10]  # Limit to 10 most recent
    }





@router.get("/maintenance/ocr-status")
async def get_ocr_status():
    """Check Google Cloud Vision OCR status and configuration."""
    try:
        from app.services.ocr_cloud import check_vision_status
        status = check_vision_status()
        return {
            "ocr_available": status.get("available", False),
            "details": status
        }
    except ImportError as e:
        return {
            "ocr_available": False,
            "details": {"error": f"OCR module not loaded: {e}"}
        }


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


@router.get("/ocr/status")
async def get_ocr_status():
    """Check if OCR is available on the server."""
    try:
        from app.services.ocr import check_tesseract_installation
        return check_tesseract_installation()
    except Exception as e:
        return {"installed": False, "error": str(e)}


# =============================================================================
# Analytics Endpoints
# =============================================================================

@router.get("/analytics/feedback-summary")
async def get_feedback_summary(
    feedback_repo: FeedbackRepository = Depends(get_feedback_repo),
):
    """Get feedback statistics summary."""
    try:
        from app.db.connection import get_async_connection
        
        async with get_async_connection() as conn:
            async with conn.cursor() as cur:
                # Count by feedback type
                await cur.execute("""
                    SELECT feedback_type, COUNT(*) as count
                    FROM answer_feedback
                    GROUP BY feedback_type
                """)
                rows = await cur.fetchall()
                
                counts = {row[0]: row[1] for row in rows}
                
                return {
                    "helpful": counts.get("helpful", 0),
                    "negative": sum(v for k, v in counts.items() if k != "helpful"),
                    "wrong_quote": counts.get("wrong_quote", 0),
                    "wrong_interpretation": counts.get("wrong_interpretation", 0),
                    "missing_context": counts.get("missing_context", 0),
                    "total": sum(counts.values()),
                }
    except Exception as e:
        logger.error(f"Failed to get feedback summary: {e}")
        return {"helpful": 0, "negative": 0, "total": 0}


@router.get("/analytics/feedback")
async def get_all_feedback(
    limit: int = 100,
    offset: int = 0,
):
    """Get all feedback with details for admin dashboard."""
    try:
        from app.db.connection import get_async_connection
        
        async with get_async_connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute("""
                    SELECT 
                        f.id,
                        f.feedback_type,
                        f.user_note,
                        f.created_at,
                        h.question,
                        h.verdict
                    FROM answer_feedback f
                    LEFT JOIN ask_history h ON f.ask_history_id = h.id
                    ORDER BY f.created_at DESC
                    LIMIT %s OFFSET %s
                """, (limit, offset))
                rows = await cur.fetchall()
                
                items = [
                    {
                        "id": row[0],
                        "feedback_type": row[1],
                        "user_note": row[2],
                        "created_at": row[3].isoformat() if row[3] else None,
                        "question": row[4][:100] + "..." if row[4] and len(row[4]) > 100 else row[4],
                        "full_question": row[4],
                        "verdict": row[5],
                    }
                    for row in rows
                ]
                
                return {"items": items, "count": len(items)}
    except Exception as e:
        logger.error(f"Failed to get feedback: {e}")
        return {"items": [], "count": 0}

