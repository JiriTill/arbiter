"""
Ingestion background jobs for processing rulebook PDFs.
"""

import logging
import time
from typing import Any

from app.jobs.queue import set_job_status
from app.services.ingestion import (
    download_pdf,
    extract_text_from_pdf,
    detect_needs_ocr,
    compute_file_hash,
    ingest_source,
)
from app.services.chunker import chunk_document
from app.services.embeddings import batch_create_embeddings
from app.db.connection import get_sync_connection
from app.db.repositories.sources import SourcesRepository
from app.db.repositories.chunks import ChunksRepository
from app.db.models import RuleChunkCreate
from rq import get_current_job

import fitz
from datetime import datetime, timedelta, timezone


logger = logging.getLogger(__name__)


def get_job_id() -> str | None:
    """Get current RQ job ID."""
    job = get_current_job()
    return job.id if job else None


def ingest_source_job(source_id: int, force: bool = False) -> dict[str, Any]:
    """
    Background job for source ingestion with progress tracking.
    
    This wraps the sync ingest_source function but provides
    detailed progress updates via Redis.
    
    Args:
        source_id: ID of the source to ingest
        force: If True, re-ingest even if already done
        
    Returns:
        Ingestion result dict
    """
    job_id = get_job_id() or f"manual-{source_id}"
    start_time = time.time()
    
    try:
        # Stage 1: Fetch source info (5%)
        set_job_status(job_id, "downloading", 5, "Fetching source information...")
        
        with get_sync_connection() as conn:
            sources_repo = SourcesRepository(conn)
            source = sources_repo.get_source_sync(source_id)
            
            if not source:
                set_job_status(job_id, "failed", 0, "Source not found", error="Source not found")
                return {"status": "error", "error": "Source not found"}
            
            if not force and source.last_ingested_at and not source.needs_reingest:
                set_job_status(job_id, "ready", 100, "Already ingested", result={"status": "already_ingested"})
                return {"status": "already_ingested"}
            
            if not source.source_url:
                set_job_status(job_id, "failed", 0, "No URL configured", error="Source has no URL")
                return {"status": "error", "error": "Source has no URL"}
        
        # Stage 2: Download PDF (10-30%)
        set_job_status(job_id, "downloading", 10, f"Downloading PDF from {source.source_url[:50]}...")
        
        try:
            pdf_bytes = download_pdf(source.source_url)
            file_hash = compute_file_hash(pdf_bytes)
        except Exception as e:
            set_job_status(job_id, "failed", 15, f"Download failed: {e}", error=str(e))
            return {"status": "error", "error": f"Download failed: {e}"}
        
        set_job_status(job_id, "downloading", 30, f"Downloaded {len(pdf_bytes):,} bytes")
        
        # Stage 3: Extract text (30-50%)
        set_job_status(job_id, "extracting", 35, "Extracting text from PDF...")
        
        try:
            with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
                total_page_count = len(doc)
            
            pages = extract_text_from_pdf(pdf_bytes)
            total_chars = sum(len(text) for _, text in pages)
        except Exception as e:
            set_job_status(job_id, "failed", 40, f"Extraction failed: {e}", error=str(e))
            return {"status": "error", "error": f"Extraction failed: {e}"}
        
        set_job_status(job_id, "extracting", 50, f"Extracted {total_chars:,} chars from {len(pages)} pages")
        
        # Check if needs OCR
        if detect_needs_ocr(pages, total_page_count):
            logger.info(f"PDF needs OCR - attempting Google Cloud Vision...")
            set_job_status(job_id, "ocr", 52, "Scanned PDF detected - starting cloud OCR...")
            
            try:
                from app.services.ocr_cloud import is_cloud_vision_available, ocr_pdf_with_vision
                
                if is_cloud_vision_available():
                    # Use Google Cloud Vision (production solution)
                    def ocr_progress(page, total, chars):
                        pct = 52 + int(28 * page / total)  # 52-80%
                        set_job_status(job_id, "ocr", pct, f"OCR page {page}/{total} ({chars:,} chars)...")
                    
                    set_job_status(job_id, "ocr", 55, f"Running Google Cloud Vision on {total_page_count} pages...")
                    pages = ocr_pdf_with_vision(pdf_bytes, progress_callback=ocr_progress)
                    total_chars = sum(len(text) for _, text in pages)
                    
                    if pages and total_chars > 100:
                        logger.info(f"Cloud Vision OCR successful: {len(pages)} pages, {total_chars} chars")
                        set_job_status(job_id, "ocr", 80, f"OCR complete: {total_chars:,} chars from {len(pages)} pages")
                        
                        # Mark as no longer needing OCR
                        with get_sync_connection() as conn:
                            with conn.cursor() as cur:
                                cur.execute(
                                    "UPDATE game_sources SET needs_ocr = FALSE, file_hash = %s, updated_at = NOW() WHERE id = %s",
                                    (file_hash, source_id)
                                )
                                conn.commit()
                    else:
                        logger.error(f"Cloud Vision extracted only {total_chars} chars")
                        set_job_status(job_id, "failed", 60, "OCR extracted insufficient text", error="OCR failed")
                        return {"status": "ocr_failed", "error": "No text extracted"}
                else:
                    # Cloud Vision not configured - mark for later
                    logger.warning("Cloud Vision not available - credentials not configured")
                    set_job_status(job_id, "failed", 55, 
                        "Scanned PDF requires OCR. Configure GOOGLE_APPLICATION_CREDENTIALS_JSON to enable.",
                        error="Cloud OCR not configured")
                    
                    with get_sync_connection() as conn:
                        with conn.cursor() as cur:
                            cur.execute(
                                "UPDATE game_sources SET needs_ocr = TRUE, file_hash = %s, updated_at = NOW() WHERE id = %s",
                                (file_hash, source_id)
                            )
                            conn.commit()
                    
                    return {"status": "needs_ocr", "error": "Cloud OCR not configured"}
                    
            except Exception as e:
                logger.error(f"Cloud Vision OCR failed: {e}")
                set_job_status(job_id, "failed", 55, f"OCR failed: {e}", error=str(e))
                
                with get_sync_connection() as conn:
                    with conn.cursor() as cur:
                        cur.execute(
                            "UPDATE game_sources SET needs_ocr = TRUE, file_hash = %s, updated_at = NOW() WHERE id = %s",
                            (file_hash, source_id)
                        )
                        conn.commit()
                
                return {"status": "ocr_failed", "error": str(e)}
        
        # Stage 4: Chunking (50-60%)
        set_job_status(job_id, "chunking", 55, "Splitting text into chunks...")
        
        chunks = chunk_document(pages, max_tokens=400, overlap=0.5)
        
        set_job_status(job_id, "chunking", 60, f"Created {len(chunks)} chunks")
        
        # Stage 5: Embedding (60-90%)
        set_job_status(job_id, "embedding", 65, f"Generating embeddings for {len(chunks)} chunks...")
        
        chunk_texts = [c.chunk_text for c in chunks]
        
        try:
            # Update progress during embedding
            batch_size = 100
            embeddings = []
            
            for i in range(0, len(chunk_texts), batch_size):
                batch = chunk_texts[i:i + batch_size]
                batch_embeddings = batch_create_embeddings(batch)
                embeddings.extend(batch_embeddings)
                
                # Update progress (65% to 85%)
                progress = 65 + int(20 * (i + len(batch)) / len(chunk_texts))
                set_job_status(job_id, "embedding", progress, 
                              f"Generated embeddings: {len(embeddings)}/{len(chunks)}")
        except Exception as e:
            logger.warning(f"Embedding failed: {e}")
            embeddings = [None] * len(chunks)
            set_job_status(job_id, "embedding", 85, "Embeddings failed - continuing without them")
        
        # Stage 6: Saving to database (90-100%)
        set_job_status(job_id, "saving", 90, "Saving chunks to database...")
        
        # Determine precedence
        precedence_map = {
            "rulebook": 1, "expansion": 2, "faq": 3, "errata": 3, "reference_card": 1,
        }
        precedence = precedence_map.get(source.source_type, 1)
        expires_at = datetime.now(timezone.utc) + timedelta(days=30)
        
        with get_sync_connection() as conn:
            chunks_repo = ChunksRepository(conn)
            
            # Delete existing chunks
            deleted = chunks_repo.delete_chunks_by_source_sync(source_id)
            
            # Insert new chunks
            for i, chunk in enumerate(chunks):
                embedding = embeddings[i] if i < len(embeddings) else None
                
                chunk_create = RuleChunkCreate(
                    source_id=source_id,
                    page_number=chunk.page_number,
                    chunk_index=chunk.chunk_index,
                    chunk_text=chunk.chunk_text,
                    embedding=embedding,
                    precedence_level=precedence,
                    expires_at=expires_at,
                )
                chunks_repo.create_chunk_sync(chunk_create)
            
            # Update source record
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE game_sources 
                    SET file_hash = %s, needs_ocr = FALSE, needs_reingest = FALSE,
                        last_ingested_at = NOW(), updated_at = NOW()
                    WHERE id = %s
                    """,
                    (file_hash, source_id)
                )
                conn.commit()
        
        duration_ms = int((time.time() - start_time) * 1000)
        
        result = {
            "status": "success",
            "source_id": source_id,
            "chunks_created": len(chunks),
            "chunks_deleted": deleted,
            "file_hash": file_hash,
            "duration_ms": duration_ms,
            "pages_processed": len(pages),
            "total_chars": total_chars,
        }
        
        set_job_status(job_id, "ready", 100, 
                      f"Ingestion complete: {len(chunks)} chunks in {duration_ms}ms",
                      result=result)
        
        logger.info(f"Ingestion job {job_id} completed: {len(chunks)} chunks")
        return result
        
    except Exception as e:
        logger.exception(f"Ingestion job {job_id} failed")
        set_job_status(job_id, "failed", 0, f"Job failed: {e}", error=str(e))
        return {"status": "error", "error": str(e)}
