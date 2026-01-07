"""
Admin API endpoints for content management and analytics.
"""

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Request
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



@router.post("/maintenance/sync-bgg-images")
async def sync_bgg_images():
    """Fetch and update game images from BoardGameGeek API.
    
    This endpoint:
    1. Gets all games with bgg_id set
    2. Fetches image URLs from BGG XML API (concurrently with rate limiting)
    3. Updates the database with the fetched URLs
    """
    import httpx
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
            sem = asyncio.Semaphore(4)
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                
                async def process_game(row):
                    game_id, name, bgg_id = row[0], row[1], row[2]
                    async with sem:
                        try:
                            # Fetch from BGG API
                            bgg_url = f"https://boardgamegeek.com/xmlapi2/thing?id={bgg_id}"
                            response = await client.get(bgg_url)
                            
                            if response.status_code != 200:
                                return {"error": f"BGG returned {response.status_code}", "game": name}
                            
                            # Parse XML
                            root = ET.fromstring(response.content)
                            image_elem = root.find(".//image")
                            thumbnail_elem = root.find(".//thumbnail")
                            
                            # Prefer thumbnail for smaller size, fallback to full image
                            image_url = None
                            if thumbnail_elem is not None and thumbnail_elem.text:
                                image_url = thumbnail_elem.text
                            elif image_elem is not None and image_elem.text:
                                image_url = image_elem.text
                            
                            if not image_url:
                                return {"error": "No image found in BGG response", "game": name}
                            
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
                            # Catch timeout and other errors
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


@router.post("/maintenance/reset-images")
async def reset_game_images():
    """Reset images to working BGG thumbnail images.
    
    This calls sync-bgg-images to fetch real images from BGG API.
    """
    # Just redirect to the sync endpoint
    return await sync_bgg_images()


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


@router.get("/proxy/image/{bgg_id}")
async def proxy_bgg_image(bgg_id: int):
    """Proxy BGG images to avoid hotlinking issues.
    
    This fetches the image from BGG's CDN and serves it.
    BGG blocks direct hotlinking but allows server-to-server requests.
    """
    import httpx
    from fastapi.responses import Response
    
    # Construct BGG image URL
    # BGG image format: https://cf.geekdo-images.com/pic{id}.jpg (small thumb)
    # For better quality, we'd need the full URL with hash, but this works for thumbnails
    bgg_url = f"https://boardgamegeek.com/xmlapi2/thing?id={bgg_id}&stats=1"
    
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=10.0) as client:
            # First, get the game info to find the image URL
            response = await client.get(bgg_url)
            if response.status_code != 200:
                # Return placeholder if BGG request fails
                return Response(
                    content=b"",
                    media_type="image/png",
                    status_code=404
                )
            
            # Parse XML to get image URL
            import xml.etree.ElementTree as ET
            root = ET.fromstring(response.content)
            image_elem = root.find(".//image")
            
            if image_elem is None or not image_elem.text:
                return Response(content=b"", media_type="image/png", status_code=404)
            
            image_url = image_elem.text
            
            # Fetch the actual image
            img_response = await client.get(image_url, headers={
                "User-Agent": "TheArbiter/1.0 (Board Game Rules)",
                "Accept": "image/*"
            })
            
            if img_response.status_code == 200:
                content_type = img_response.headers.get("content-type", "image/jpeg")
                return Response(
                    content=img_response.content,
                    media_type=content_type,
                    headers={"Cache-Control": "public, max-age=86400"}  # Cache for 1 day
                )
            
    except Exception as e:
        logger.error(f"BGG image proxy error for {bgg_id}: {e}")
    
    # Return 404 if anything fails
    return Response(content=b"", media_type="image/png", status_code=404)


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
                
                counts = {row["feedback_type"]: row["count"] for row in rows}
                
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
                        "id": row["id"],
                        "feedback_type": row["feedback_type"],
                        "user_note": row["user_note"],
                        "created_at": row["created_at"].isoformat() if row["created_at"] else None,
                        "question": row["question"][:100] + "..." if row["question"] and len(row["question"]) > 100 else row["question"],
                        "full_question": row["question"],
                        "verdict": row["verdict"],
                    }
                    for row in rows
                ]
                
                return {"items": items, "count": len(items)}
    except Exception as e:
        logger.error(f"Failed to get feedback: {e}")
        return {"items": [], "count": 0}

