"""
Override detector for identifying when expansion rules override base rules.

This runs ONCE during ingestion to minimize LLM costs.
"""

import json
import logging
import re
from typing import Any

from openai import OpenAI

from app.config import get_settings
from app.db.models import RuleChunk, RuleChunkSearchResult
from app.services.embeddings import create_embedding


logger = logging.getLogger(__name__)


# Override detection configuration
SIMILARITY_THRESHOLD = 0.82  # Minimum similarity to consider as candidate
MAX_CANDIDATES_PER_CHUNK = 3  # Max base chunks to consider
OVERRIDE_MODEL = "gpt-4o-mini"

# Regex pattern for override keywords
OVERRIDE_KEYWORDS_PATTERN = re.compile(
    r'\b(instead|replaces?|ignores?|supersedes?|overrides?|'
    r'in\s+place\s+of|rather\s+than|no\s+longer|'
    r'use\s+this\s+(rule|ability)|takes?\s+precedence|'
    r'now\s+(you|players?|the)|changes?\s+to)\b',
    re.IGNORECASE
)


def get_openai_client() -> OpenAI:
    """Get configured OpenAI client."""
    settings = get_settings()
    if not settings.openai_api_key:
        raise ValueError("OPENAI_API_KEY not configured")
    return OpenAI(api_key=settings.openai_api_key)


def has_override_keywords(text: str) -> bool:
    """Check if text contains override-indicating keywords."""
    return bool(OVERRIDE_KEYWORDS_PATTERN.search(text))


def classify_override(
    expansion_chunk: RuleChunk,
    base_chunk: RuleChunk,
) -> dict[str, Any]:
    """
    Use LLM to classify if expansion chunk overrides base chunk.
    
    Args:
        expansion_chunk: The expansion rule chunk
        base_chunk: The base game rule chunk
        
    Returns:
        Dict with is_override, confidence, evidence_phrase
    """
    exp_text = expansion_chunk.chunk_text[:800]
    base_text = base_chunk.chunk_text[:800]
    
    prompt = f"""Compare these two rule excerpts:

BASE RULE (original game):
{base_text}

EXPANSION RULE (new content):
{exp_text}

Question: Does the expansion rule OVERRIDE/REPLACE the base rule?
An override means the expansion rule changes how something works compared to the base rule.

Respond with JSON only:
{{
  "is_override": true/false,
  "confidence": 0-100,
  "evidence_phrase": "brief quote showing override language (or empty if not override)"
}}"""

    client = get_openai_client()
    
    try:
        response = client.chat.completions.create(
            model=OVERRIDE_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You analyze board game rules to detect when expansion rules override base game rules. Be conservative - only mark as override if there's clear evidence. Output JSON only."
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=150,
            temperature=0.1,
        )
        
        content = response.choices[0].message.content.strip()
        
        # Parse JSON response
        try:
            result = json.loads(content)
        except json.JSONDecodeError:
            # Try to extract JSON
            json_match = re.search(r'\{[^{}]*\}', content)
            if json_match:
                result = json.loads(json_match.group(0))
            else:
                logger.warning(f"Failed to parse LLM response: {content[:100]}")
                result = {"is_override": False, "confidence": 0, "evidence_phrase": ""}
        
        return {
            "is_override": result.get("is_override", False),
            "confidence": min(100, max(0, int(result.get("confidence", 0)))),
            "evidence_phrase": str(result.get("evidence_phrase", ""))[:200],
        }
        
    except Exception as e:
        logger.error(f"Override classification failed: {e}")
        return {
            "is_override": False,
            "confidence": 0,
            "evidence_phrase": "",
            "error": str(e),
        }


def find_similar_base_chunks(
    expansion_chunk: RuleChunk,
    base_chunks: list[RuleChunk],
    limit: int = MAX_CANDIDATES_PER_CHUNK,
) -> list[tuple[RuleChunk, float]]:
    """
    Find base chunks most similar to an expansion chunk.
    
    Uses embedding similarity for efficient filtering.
    
    Args:
        expansion_chunk: Expansion chunk to find matches for
        base_chunks: List of base game chunks
        limit: Maximum similar chunks to return
        
    Returns:
        List of (chunk, similarity_score) tuples
    """
    if not base_chunks:
        return []
    
    # Get expansion chunk embedding
    exp_embedding = expansion_chunk.embedding
    if not exp_embedding:
        exp_embedding = create_embedding(expansion_chunk.chunk_text)
    
    # Calculate similarity with each base chunk
    similarities = []
    for base in base_chunks:
        if not base.embedding:
            continue
        
        # Cosine similarity
        sim = cosine_similarity(exp_embedding, base.embedding)
        similarities.append((base, sim))
    
    # Sort by similarity descending
    similarities.sort(key=lambda x: x[1], reverse=True)
    
    return similarities[:limit]


def cosine_similarity(vec1: list[float], vec2: list[float]) -> float:
    """Calculate cosine similarity between two vectors."""
    if len(vec1) != len(vec2):
        return 0.0
    
    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    norm1 = sum(a * a for a in vec1) ** 0.5
    norm2 = sum(b * b for b in vec2) ** 0.5
    
    if norm1 == 0 or norm2 == 0:
        return 0.0
    
    return dot_product / (norm1 * norm2)


def detect_overrides(
    expansion_chunks: list[RuleChunk],
    base_chunks: list[RuleChunk],
    min_confidence: int = 70,
) -> list[dict[str, Any]]:
    """
    Detect which expansion chunks override base chunks.
    
    Uses a cost-optimized approach:
    1. Find semantically similar base chunks (embedding-based)
    2. Filter by similarity threshold
    3. Check for override keywords (regex)
    4. Only call LLM for high-probability candidates
    
    Args:
        expansion_chunks: Chunks from the expansion source
        base_chunks: Chunks from the base game source
        min_confidence: Minimum confidence to include in results
        
    Returns:
        List of override relationships
    """
    if not expansion_chunks or not base_chunks:
        return []
    
    overrides = []
    llm_calls = 0
    keyword_matches = 0
    
    logger.info(f"Detecting overrides: {len(expansion_chunks)} expansion chunks vs {len(base_chunks)} base chunks")
    
    for exp_chunk in expansion_chunks:
        # Step 1: Check for override keywords (cheap)
        if not has_override_keywords(exp_chunk.chunk_text):
            continue
        
        keyword_matches += 1
        
        # Step 2: Find similar base chunks (embedding-based, no LLM)
        similar_base = find_similar_base_chunks(
            expansion_chunk=exp_chunk,
            base_chunks=base_chunks,
            limit=MAX_CANDIDATES_PER_CHUNK,
        )
        
        # Step 3: Filter by similarity threshold
        candidates = [(c, s) for c, s in similar_base if s >= SIMILARITY_THRESHOLD]
        
        if not candidates:
            continue
        
        # Step 4: Only classify the BEST candidate (cost optimization)
        best_base, best_similarity = candidates[0]
        
        logger.debug(
            f"Checking exp_chunk {exp_chunk.id} vs base_chunk {best_base.id} "
            f"(similarity: {best_similarity:.3f})"
        )
        
        llm_calls += 1
        result = classify_override(exp_chunk, best_base)
        
        if result["is_override"] and result["confidence"] >= min_confidence:
            overrides.append({
                "expansion_chunk_id": exp_chunk.id,
                "overrides_chunk_id": best_base.id,
                "confidence": result["confidence"],
                "evidence": result["evidence_phrase"],
                "similarity": best_similarity,
            })
            
            logger.info(
                f"Override detected: chunk {exp_chunk.id} overrides {best_base.id} "
                f"(confidence: {result['confidence']})"
            )
    
    logger.info(
        f"Override detection complete: "
        f"{len(overrides)} overrides found, "
        f"{keyword_matches} keyword matches, "
        f"{llm_calls} LLM calls"
    )
    
    return overrides


def save_override_relationships(
    overrides: list[dict[str, Any]],
) -> int:
    """
    Save detected override relationships to the database.
    
    Args:
        overrides: List of override dicts from detect_overrides
        
    Returns:
        Number of relationships saved
    """
    from app.db.connection import get_sync_connection
    
    if not overrides:
        return 0
    
    saved = 0
    
    with get_sync_connection() as conn:
        with conn.cursor() as cur:
            for override in overrides:
                try:
                    cur.execute("""
                        UPDATE rule_chunks
                        SET 
                            overrides_chunk_id = %s,
                            override_confidence = %s,
                            override_evidence = %s
                        WHERE id = %s
                    """, (
                        override["overrides_chunk_id"],
                        override["confidence"],
                        override["evidence"],
                        override["expansion_chunk_id"],
                    ))
                    saved += 1
                except Exception as e:
                    logger.error(f"Failed to save override {override}: {e}")
            
            conn.commit()
    
    logger.info(f"Saved {saved} override relationships")
    return saved


def detect_and_save_overrides(
    expansion_source_id: int,
    base_source_ids: list[int],
) -> dict[str, Any]:
    """
    Detect and save overrides for an expansion source.
    
    This is the main entry point called after ingestion.
    
    Args:
        expansion_source_id: ID of the ingested expansion source
        base_source_ids: IDs of base game sources to compare against
        
    Returns:
        Summary of detection results
    """
    from app.db.connection import get_sync_connection
    
    logger.info(f"Running override detection for source {expansion_source_id}")
    
    result = {
        "expansion_source_id": expansion_source_id,
        "base_source_ids": base_source_ids,
        "overrides_detected": 0,
        "overrides_saved": 0,
        "llm_calls": 0,
    }
    
    try:
        with get_sync_connection() as conn:
            with conn.cursor() as cur:
                # Get expansion chunks
                cur.execute("""
                    SELECT * FROM rule_chunks
                    WHERE source_id = %s
                    AND embedding IS NOT NULL
                """, (expansion_source_id,))
                exp_rows = cur.fetchall()
                expansion_chunks = [RuleChunk.model_validate(dict(r)) for r in exp_rows]
                
                if not expansion_chunks:
                    logger.warning(f"No chunks found for expansion source {expansion_source_id}")
                    return result
                
                # Get base chunks
                if base_source_ids:
                    cur.execute("""
                        SELECT * FROM rule_chunks
                        WHERE source_id = ANY(%s)
                        AND embedding IS NOT NULL
                    """, (base_source_ids,))
                    base_rows = cur.fetchall()
                    base_chunks = [RuleChunk.model_validate(dict(r)) for r in base_rows]
                else:
                    base_chunks = []
                
                if not base_chunks:
                    logger.warning(f"No base chunks found for sources {base_source_ids}")
                    return result
        
        # Detect overrides
        overrides = detect_overrides(expansion_chunks, base_chunks)
        result["overrides_detected"] = len(overrides)
        
        # Save to database
        if overrides:
            saved = save_override_relationships(overrides)
            result["overrides_saved"] = saved
        
        return result
        
    except Exception as e:
        logger.error(f"Override detection failed: {e}")
        result["error"] = str(e)
        return result
