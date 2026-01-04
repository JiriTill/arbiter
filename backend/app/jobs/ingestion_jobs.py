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
            logger.info(f"PDF needs OCR - attempting OCR extraction...")
            set_job_status(job_id, "ocr", 52, "Scanned PDF detected - running OCR (this may take a while)...")
            
            try:
                from app.services.ocr import ocr_pdf_bytes, is_ocr_available
                
                if not is_ocr_available():
                    logger.error("OCR not available - pytesseract not installed")
                    with get_sync_connection() as conn:
                        with conn.cursor() as cur:
                            cur.execute(
                                "UPDATE game_sources SET needs_ocr = TRUE, file_hash = %s, updated_at = NOW() WHERE id = %s",
                                (file_hash, source_id)
                            )
                            conn.commit()
                    set_job_status(job_id, "failed", 52, "OCR not available on server", error="OCR not available")
                    return {"status": "needs_ocr", "error": "OCR not available"}
                
                # Run OCR on the PDF with progress callback
                def ocr_progress(page, total, chars):
                    # Map OCR progress to 55-75% range
                    pct = 55 + int(20 * page / total)
                    set_job_status(job_id, "ocr", pct, f"OCR page {page}/{total} ({chars:,} chars so far)...")
                
                set_job_status(job_id, "ocr", 55, f"Starting OCR on {total_page_count} pages (memory-optimized)...")
                pages = ocr_pdf_bytes(pdf_bytes, dpi=150, progress_callback=ocr_progress)
                total_chars = sum(len(text) for _, text in pages)
                
                if not pages or total_chars < 100:
                    logger.error(f"OCR failed to extract text: {total_chars} chars from {len(pages)} pages")
                    with get_sync_connection() as conn:
                        with conn.cursor() as cur:
                            cur.execute(
                                "UPDATE game_sources SET needs_ocr = TRUE, file_hash = %s, updated_at = NOW() WHERE id = %s",
                                (file_hash, source_id)
                            )
                            conn.commit()
                    set_job_status(job_id, "failed", 55, "OCR extraction failed", error="OCR extracted no text")
                    return {"status": "ocr_failed", "error": "OCR extracted no text"}
                
                logger.info(f"OCR successful: {len(pages)} pages, {total_chars} chars")
                set_job_status(job_id, "ocr", 60, f"OCR complete: {total_chars:,} chars from {len(pages)} pages")
                
            except ImportError as e:
                logger.error(f"OCR libraries not installed: {e}")
                with get_sync_connection() as conn:
                    with conn.cursor() as cur:
                        cur.execute(
                            "UPDATE game_sources SET needs_ocr = TRUE, file_hash = %s, updated_at = NOW() WHERE id = %s",
                            (file_hash, source_id)
                        )
                        conn.commit()
                set_job_status(job_id, "failed", 52, "OCR libraries not installed", error=str(e))
                return {"status": "needs_ocr", "error": str(e)}
            except Exception as e:
                logger.error(f"OCR failed: {e}")
                with get_sync_connection() as conn:
                    with conn.cursor() as cur:
                        cur.execute(
                            "UPDATE game_sources SET needs_ocr = TRUE, file_hash = %s, updated_at = NOW() WHERE id = %s",
                            (file_hash, source_id)
                        )
                        conn.commit()
                set_job_status(job_id, "failed", 55, f"OCR failed: {e}", error=str(e))
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
