"""
Citation verification service with exact and fuzzy matching.

This module provides two-pass verification:
1. Exact match: Checks if quote is a substring of the chunk
2. Fuzzy match: Allows small edits (typos, whitespace differences)
"""

import re
import logging
from typing import Any

from app.db.models import RuleChunk, RuleChunkSearchResult
from app.services.levenshtein import levenshtein_distance, find_best_match_window


logger = logging.getLogger(__name__)


def normalize_text(text: str) -> str:
    """
    Normalize text for comparison.
    
    - Collapses multiple whitespace to single space
    - Strips leading/trailing whitespace
    - Lowercases for comparison
    
    Args:
        text: Input text
        
    Returns:
        Normalized text
    """
    if not text:
        return ""
    
    # Collapse all whitespace (including newlines, tabs) to single space
    normalized = re.sub(r'\s+', ' ', text)
    # Strip and lowercase
    normalized = normalized.strip().lower()
    
    return normalized


def normalize_for_display(text: str) -> str:
    """
    Normalize text but preserve case for display.
    
    Args:
        text: Input text
        
    Returns:
        Normalized text with preserved case
    """
    if not text:
        return ""
    
    # Collapse whitespace but keep case
    return re.sub(r'\s+', ' ', text).strip()


def verify_citation(
    quote: str,
    chunk_id: int,
    chunks: list[RuleChunk | RuleChunkSearchResult],
    max_exact_distance: int = 0,
    max_fuzzy_distance: int = 8,
    max_fuzzy_percent: float = 0.02,
) -> dict[str, Any]:
    """
    Verify a citation quote against a chunk's text.
    
    Performs two-pass verification:
    1. Exact: Checks if normalized quote is substring of normalized chunk
    2. Fuzzy: Allows small edit distance for typos/formatting
    
    Args:
        quote: The quoted text to verify
        chunk_id: The ID of the chunk the quote claims to be from
        chunks: List of available chunks to search
        max_exact_distance: Max Levenshtein distance for "exact" match (0 = true exact)
        max_fuzzy_distance: Max absolute Levenshtein distance for fuzzy match
        max_fuzzy_percent: Max Levenshtein distance as percentage of quote length
        
    Returns:
        dict with:
            - verified: bool
            - method: "exact" | "fuzzy" | None
            - distance: int (for fuzzy matches)
            - matched_text: str (the actual text matched)
            - chunk_id: int
    """
    result = {
        "verified": False,
        "method": None,
        "distance": None,
        "matched_text": None,
        "chunk_id": chunk_id,
    }
    
    if not quote or not quote.strip():
        logger.warning("Empty quote provided for verification")
        return result
    
    # Find the target chunk
    target_chunk = None
    for chunk in chunks:
        if chunk.id == chunk_id:
            target_chunk = chunk
            break
    
    if not target_chunk:
        logger.warning(f"Chunk {chunk_id} not found in provided chunks")
        # Try to find quote in ANY chunk
        return verify_citation_in_any_chunk(quote, chunks, max_fuzzy_distance, max_fuzzy_percent)
    
    chunk_text = target_chunk.chunk_text
    if not chunk_text:
        return result
    
    # Normalize texts for comparison
    normalized_quote = normalize_text(quote)
    normalized_chunk = normalize_text(chunk_text)
    
    # ========================================================================
    # Pass A: Exact Match
    # ========================================================================
    
    if normalized_quote in normalized_chunk:
        result["verified"] = True
        result["method"] = "exact"
        result["distance"] = 0
        result["matched_text"] = quote
        logger.debug(f"Citation verified (exact): chunk_id={chunk_id}")
        return result
    
    # ========================================================================
    # Pass B: Fuzzy Match
    # ========================================================================
    
    # Find best matching window in the chunk
    best_match, start_idx, distance = find_best_match_window(normalized_quote, normalized_chunk)
    
    # Calculate thresholds
    max_allowed_distance = min(
        max_fuzzy_distance,
        int(len(normalized_quote) * max_fuzzy_percent)
    )
    # Ensure at least some tolerance
    max_allowed_distance = max(max_allowed_distance, max_fuzzy_distance)
    
    if distance <= max_allowed_distance:
        result["verified"] = True
        result["method"] = "fuzzy"
        result["distance"] = distance
        # Get the original (non-normalized) matched text
        result["matched_text"] = chunk_text[start_idx:start_idx + len(best_match)]
        logger.debug(f"Citation verified (fuzzy): chunk_id={chunk_id}, distance={distance}")
        return result
    
    logger.warning(
        f"Citation verification failed: chunk_id={chunk_id}, "
        f"distance={distance}, max_allowed={max_allowed_distance}"
    )
    return result


def verify_citation_in_any_chunk(
    quote: str,
    chunks: list[RuleChunk | RuleChunkSearchResult],
    max_fuzzy_distance: int = 8,
    max_fuzzy_percent: float = 0.02,
) -> dict[str, Any]:
    """
    Try to find and verify a quote in any of the provided chunks.
    
    Used as fallback when specified chunk_id doesn't contain the quote.
    
    Args:
        quote: The quoted text to verify
        chunks: List of chunks to search
        max_fuzzy_distance: Max absolute edit distance
        max_fuzzy_percent: Max edit distance as percentage
        
    Returns:
        Verification result dict
    """
    result = {
        "verified": False,
        "method": None,
        "distance": None,
        "matched_text": None,
        "chunk_id": None,
    }
    
    normalized_quote = normalize_text(quote)
    
    # First try exact match in any chunk
    for chunk in chunks:
        if not chunk.chunk_text:
            continue
        
        normalized_chunk = normalize_text(chunk.chunk_text)
        
        if normalized_quote in normalized_chunk:
            result["verified"] = True
            result["method"] = "exact"
            result["distance"] = 0
            result["matched_text"] = quote
            result["chunk_id"] = chunk.id
            logger.info(f"Quote found in different chunk: {chunk.id}")
            return result
    
    # Then try fuzzy match
    best_overall_distance = float('inf')
    best_chunk_id = None
    best_match_text = None
    
    for chunk in chunks:
        if not chunk.chunk_text:
            continue
        
        normalized_chunk = normalize_text(chunk.chunk_text)
        best_match, start_idx, distance = find_best_match_window(normalized_quote, normalized_chunk)
        
        if distance < best_overall_distance:
            best_overall_distance = distance
            best_chunk_id = chunk.id
            best_match_text = best_match
    
    # Check if best fuzzy match passes threshold
    max_allowed = max(
        max_fuzzy_distance,
        int(len(normalized_quote) * max_fuzzy_percent)
    )
    
    if best_overall_distance <= max_allowed:
        result["verified"] = True
        result["method"] = "fuzzy"
        result["distance"] = int(best_overall_distance)
        result["matched_text"] = best_match_text
        result["chunk_id"] = best_chunk_id
        logger.info(f"Quote fuzzy-matched in different chunk: {best_chunk_id}")
        return result
    
    return result


def get_relevant_sections(
    chunks: list[RuleChunk | RuleChunkSearchResult],
    max_sections: int = 3,
    preview_length: int = 200,
) -> list[dict[str, Any]]:
    """
    Get relevant section previews for fallback response.
    
    Args:
        chunks: List of chunks to extract from
        max_sections: Maximum number of sections to return
        preview_length: Maximum length of each preview
        
    Returns:
        List of section dicts with chunk_id, page, text, source_type
    """
    sections = []
    
    for chunk in chunks[:max_sections]:
        text = normalize_for_display(chunk.chunk_text or "")
        if len(text) > preview_length:
            text = text[:preview_length].rsplit(' ', 1)[0] + "..."
        
        # Get source_type from chunk metadata if available
        source_type = "rulebook"  # Default
        if hasattr(chunk, 'metadata') and chunk.metadata:
            source_type = chunk.metadata.get('source_type', 'rulebook')
        
        sections.append({
            "chunk_id": chunk.id,
            "page": chunk.page_number,
            "text": text,
            "source_type": source_type,
        })
    
    return sections
