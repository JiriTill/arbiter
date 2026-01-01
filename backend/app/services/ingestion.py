"""
PDF ingestion service for extracting and chunking rulebook text.
Handles download, text extraction, OCR detection, chunking, and embedding.
"""

import hashlib
import logging
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

import fitz  # PyMuPDF
import httpx

from app.config import get_settings
from app.db.connection import get_sync_connection
from app.db.repositories.sources import SourcesRepository
from app.db.repositories.chunks import ChunksRepository
from app.db.models import GameSource, RuleChunkCreate
from app.services.chunker import chunk_document, Chunk
from app.services.embeddings import batch_create_embeddings


# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class IngestionResult:
    """Result of ingestion operation."""
    status: str  # "success", "needs_ocr", "error", "no_url", "already_ingested"
    source_id: int
    chunks_created: int = 0
    chunks_deleted: int = 0
    file_hash: str | None = None
    duration_ms: int = 0
    error: str | None = None
    pages_processed: int = 0
    total_chars: int = 0


# OCR detection threshold
# If less than 50 chars per page on average, likely scanned
OCR_THRESHOLD_CHARS_PER_PAGE = 50
MIN_PAGES_FOR_OCR_CHECK = 3


def compute_file_hash(content: bytes) -> str:
    """Compute SHA-256 hash of file content."""
    return hashlib.sha256(content).hexdigest()


def download_pdf(url: str, timeout: float = 30.0) -> bytes:
    """
    Download PDF from URL.
    
    Args:
        url: URL to download from
        timeout: Request timeout in seconds
        
    Returns:
        PDF content as bytes
        
    Raises:
        httpx.HTTPError: On network/HTTP errors
        ValueError: If response is not a PDF
    """
    logger.info(f"Downloading PDF from: {url[:100]}...")
    
    with httpx.Client(timeout=timeout, follow_redirects=True) as client:
        response = client.get(url)
        response.raise_for_status()
        
        content_type = response.headers.get("content-type", "").lower()
        
        # Validate it looks like a PDF
        content = response.content
        if not content.startswith(b'%PDF'):
            # Some servers don't set correct content-type
            # Trust the magic bytes over content-type
            if b'%PDF' not in content[:1024]:
                raise ValueError(f"Response does not appear to be a PDF (content-type: {content_type})")
        
        logger.info(f"Downloaded {len(content):,} bytes")
        return content


def extract_text_from_pdf(pdf_bytes: bytes) -> list[tuple[int, str]]:
    """
    Extract text from PDF bytes, page by page.
    
    Args:
        pdf_bytes: PDF file content
        
    Returns:
        List of (page_number, page_text) tuples (1-indexed page numbers)
    """
    pages: list[tuple[int, str]] = []
    
    with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
        for page_num, page in enumerate(doc, start=1):
            text = page.get_text("text")
            # Clean up text
            text = text.strip()
            if text:
                pages.append((page_num, text))
    
    return pages


def detect_needs_ocr(pages: list[tuple[int, str]], total_page_count: int) -> bool:
    """
    Detect if PDF is likely scanned and needs OCR.
    
    Args:
        pages: Extracted pages with text
        total_page_count: Total pages in PDF
        
    Returns:
        True if PDF appears to be scanned/image-based
    """
    if total_page_count < MIN_PAGES_FOR_OCR_CHECK:
        # Too few pages to reliably detect
        # Default to not needing OCR if we got any text
        total_chars = sum(len(text) for _, text in pages)
        return total_chars < 100
    
    # Calculate average chars per page
    total_chars = sum(len(text) for _, text in pages)
    avg_chars_per_page = total_chars / total_page_count if total_page_count > 0 else 0
    
    logger.info(f"OCR detection: {total_chars} chars across {total_page_count} pages "
                f"({avg_chars_per_page:.1f} chars/page)")
    
    return avg_chars_per_page < OCR_THRESHOLD_CHARS_PER_PAGE


def ingest_source(
    source_id: int,
    force: bool = False,
    save_chunks: bool = True,
) -> dict[str, Any]:
    """
    Ingest a source document: download, extract, chunk, and store.
    
    Args:
        source_id: ID of the source to ingest
        force: If True, re-ingest even if already done
        save_chunks: If True, save chunks to database
        
    Returns:
        Dict with status and metadata
    """
    start_time = time.time()
    
    try:
        with get_sync_connection() as conn:
            # Get source record
            sources_repo = SourcesRepository(conn)
            source = sources_repo.get_source_sync(source_id)
            
            if not source:
                return IngestionResult(
                    status="error",
                    source_id=source_id,
                    error="Source not found",
                ).__dict__
            
            # Check if already ingested (unless forced)
            if not force and source.last_ingested_at and not source.needs_reingest:
                return IngestionResult(
                    status="already_ingested",
                    source_id=source_id,
                    file_hash=source.file_hash,
                ).__dict__
            
            # Check for URL
            if not source.source_url:
                return IngestionResult(
                    status="no_url",
                    source_id=source_id,
                    error="Source has no URL configured",
                ).__dict__
            
            # Download PDF
            try:
                pdf_bytes = download_pdf(source.source_url)
            except httpx.TimeoutException:
                return IngestionResult(
                    status="error",
                    source_id=source_id,
                    error=f"Timeout downloading PDF (30s)",
                    duration_ms=int((time.time() - start_time) * 1000),
                ).__dict__
            except httpx.HTTPStatusError as e:
                return IngestionResult(
                    status="error",
                    source_id=source_id,
                    error=f"HTTP error {e.response.status_code}: {e.response.reason_phrase}",
                    duration_ms=int((time.time() - start_time) * 1000),
                ).__dict__
            except (httpx.HTTPError, ValueError) as e:
                return IngestionResult(
                    status="error",
                    source_id=source_id,
                    error=str(e),
                    duration_ms=int((time.time() - start_time) * 1000),
                ).__dict__
            
            # Compute file hash
            file_hash = compute_file_hash(pdf_bytes)
            
            # Check if content changed
            if not force and source.file_hash == file_hash:
                logger.info(f"Source {source_id} unchanged (hash match)")
                return IngestionResult(
                    status="unchanged",
                    source_id=source_id,
                    file_hash=file_hash,
                    duration_ms=int((time.time() - start_time) * 1000),
                ).__dict__
            
            # Extract text
            try:
                with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
                    total_page_count = len(doc)
                
                pages = extract_text_from_pdf(pdf_bytes)
            except Exception as e:
                return IngestionResult(
                    status="error",
                    source_id=source_id,
                    error=f"Failed to parse PDF: {e}",
                    duration_ms=int((time.time() - start_time) * 1000),
                ).__dict__
            
            total_chars = sum(len(text) for _, text in pages)
            
            # Check if needs OCR
            if detect_needs_ocr(pages, total_page_count):
                # Update source to mark as needing OCR
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        UPDATE game_sources 
                        SET needs_ocr = TRUE, file_hash = %s, updated_at = NOW()
                        WHERE id = %s
                        """,
                        (file_hash, source_id)
                    )
                    conn.commit()
                
                return IngestionResult(
                    status="needs_ocr",
                    source_id=source_id,
                    file_hash=file_hash,
                    pages_processed=total_page_count,
                    total_chars=total_chars,
                    duration_ms=int((time.time() - start_time) * 1000),
                ).__dict__
            
            # Chunk the text
            chunks = chunk_document(pages, max_tokens=400, overlap=0.5)
            
            logger.info(f"Created {len(chunks)} chunks from {len(pages)} pages")
            
            chunks_created = 0
            chunks_deleted = 0
            
            if save_chunks and chunks:
                chunks_repo = ChunksRepository(conn)
                
                # Delete existing chunks for this source
                chunks_deleted = chunks_repo.delete_chunks_by_source_sync(source_id)
                logger.info(f"Deleted {chunks_deleted} existing chunks")
                
                # Determine precedence level based on source type
                precedence_map = {
                    "rulebook": 1,
                    "expansion": 2,
                    "faq": 3,
                    "errata": 3,
                    "reference_card": 1,
                }
                precedence = precedence_map.get(source.source_type, 1)
                
                # Generate embeddings for all chunks
                chunk_texts = [chunk.chunk_text for chunk in chunks]
                logger.info(f"Generating embeddings for {len(chunk_texts)} chunks...")
                
                try:
                    embeddings = batch_create_embeddings(chunk_texts)
                    logger.info(f"Generated {len(embeddings)} embeddings")
                except Exception as e:
                    logger.error(f"Failed to generate embeddings: {e}")
                    # Continue without embeddings - they can be added later
                    embeddings = [None] * len(chunks)
                
                # Calculate expiration (30 days from now)
                expires_at = datetime.now(timezone.utc) + timedelta(days=30)
                
                # Create new chunks with embeddings
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
                    chunks_created += 1
                
                logger.info(f"Created {chunks_created} new chunks with embeddings")
            
            # Update source record
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE game_sources 
                    SET file_hash = %s, 
                        needs_ocr = FALSE, 
                        needs_reingest = FALSE,
                        last_ingested_at = NOW(),
                        updated_at = NOW()
                    WHERE id = %s
                    """,
                    (file_hash, source_id)
                )
                conn.commit()
            
            # TRIGGER OVERRIDE DETECTION
            # If this is an expansion, check for overrides against base game rules
            if precedence == 2:  # Expansion
                try:
                    logger.info(f"Triggering override detection for expansion source {source_id}")
                    # Find base sources for this game
                    with conn.cursor() as cur:
                        cur.execute("""
                            SELECT id FROM game_sources
                            WHERE game_id = %s
                            AND source_type IN ('rulebook', 'reference_card')
                            AND id != %s
                        """, (source.game_id, source_id))
                        base_rows = cur.fetchall()
                        base_source_ids = [r[0] for r in base_rows]
                    
                    if base_source_ids:
                        from app.services.override_detector import detect_and_save_overrides
                        override_result = detect_and_save_overrides(source_id, base_source_ids)
                        logger.info(f"Override detection result: {override_result}")
                except Exception as e:
                    logger.error(f"Failed to run override detection: {e}")
            
            duration_ms = int((time.time() - start_time) * 1000)
            
            return IngestionResult(
                status="success",
                source_id=source_id,
                chunks_created=chunks_created,
                chunks_deleted=chunks_deleted,
                file_hash=file_hash,
                duration_ms=duration_ms,
                pages_processed=len(pages),
                total_chars=total_chars,
            ).__dict__
    
    except Exception as e:
        logger.exception(f"Unexpected error ingesting source {source_id}")
        return IngestionResult(
            status="error",
            source_id=source_id,
            error=f"Unexpected error: {e}",
            duration_ms=int((time.time() - start_time) * 1000),
        ).__dict__


def ingest_all_pending(limit: int = 10) -> list[dict[str, Any]]:
    """
    Ingest all sources that need processing.
    
    Args:
        limit: Maximum sources to process in one batch
        
    Returns:
        List of ingestion results
    """
    results: list[dict[str, Any]] = []
    
    with get_sync_connection() as conn:
        sources_repo = SourcesRepository(conn)
        
        # Get sources needing reingest
        sources = sources_repo.get_sources_needing_reingest_sync(limit)
        
        if not sources:
            logger.info("No sources need ingestion")
            return results
        
        logger.info(f"Found {len(sources)} sources to ingest")
    
    # Process each source (outside connection context)
    for source in sources:
        logger.info(f"Ingesting source {source.id}: {source.edition} ({source.source_type})")
        result = ingest_source(source.id)
        results.append(result)
        logger.info(f"  Result: {result['status']}")
    
    return results
