"""
Conflict detector for identifying contradictory rules.
"""

import logging
import json
from typing import Any

from openai import OpenAI

from app.config import get_settings
from app.db.models import RuleChunk, RuleChunkSearchResult


logger = logging.getLogger(__name__)


# Model for conflict detection
CONFLICT_MODEL = "gpt-4o-mini"


def get_openai_client() -> OpenAI:
    """Get configured OpenAI client."""
    settings = get_settings()
    if not settings.openai_api_key:
        raise ValueError("OPENAI_API_KEY not configured")
    return OpenAI(api_key=settings.openai_api_key)


def detect_conflict(
    chunk1: RuleChunk | RuleChunkSearchResult,
    chunk2: RuleChunk | RuleChunkSearchResult,
    question: str,
) -> dict[str, Any]:
    """
    Detect if two rule chunks contradict each other.
    
    Uses LLM to analyze if the chunks provide contradictory answers
    to the given question.
    
    Args:
        chunk1: First chunk (typically higher precedence)
        chunk2: Second chunk (typically lower precedence)
        question: The question being answered
        
    Returns:
        Dict with:
        - is_conflict: bool - True if contradictory
        - explanation: str - Explanation of the conflict
        - resolution: str - How the conflict should be resolved
    """
    # Get text extracts
    text1 = chunk1.chunk_text[:500]
    text2 = chunk2.chunk_text[:500]
    
    # Get source info
    prec1 = getattr(chunk1, 'precedence_level', 1)
    prec2 = getattr(chunk2, 'precedence_level', 1)
    
    source1_type = _get_source_type_label(prec1)
    source2_type = _get_source_type_label(prec2)
    
    prompt = f"""Analyze if these two rule excerpts provide contradictory information for the question.

Question: {question}

Excerpt 1 ({source1_type}):
{text1}

Excerpt 2 ({source2_type}):
{text2}

Determine if these excerpts contradict each other regarding the question.

Respond with JSON:
{{
  "is_conflict": true/false,
  "explanation": "Brief explanation if conflict exists",
  "resolution": "How to resolve the conflict (e.g., 'Expansion overrides base rules')"
}}

Only JSON, no other text."""

    client = get_openai_client()
    
    try:
        response = client.chat.completions.create(
            model=CONFLICT_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are a rules expert analyzing if two game rule excerpts contradict each other. Be concise."
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=200,
            temperature=0.1,
        )
        
        content = response.choices[0].message.content.strip()
        
        # Parse JSON
        try:
            result = json.loads(content)
        except json.JSONDecodeError:
            # Try to extract JSON
            import re
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group(0))
            else:
                result = {"is_conflict": False, "explanation": "", "resolution": ""}
        
        return {
            "is_conflict": result.get("is_conflict", False),
            "explanation": result.get("explanation", ""),
            "resolution": result.get("resolution", ""),
            "chunk1_id": chunk1.id,
            "chunk2_id": chunk2.id,
        }
        
    except Exception as e:
        logger.error(f"Conflict detection failed: {e}")
        return {
            "is_conflict": False,
            "explanation": "",
            "resolution": "",
            "error": str(e),
        }


def _get_source_type_label(precedence_level: int) -> str:
    """Get human-readable source type from precedence level."""
    if precedence_level == 3:
        return "Errata/FAQ"
    elif precedence_level == 2:
        return "Expansion"
    else:
        return "Base Rulebook"


def check_top_chunks_for_conflict(
    ranked_chunks: list[tuple],  # List of (chunk, score) or ScoredChunk
    question: str,
    score_threshold: float = 0.05,
) -> dict[str, Any] | None:
    """
    Check if top 2 chunks have a potential conflict.
    
    Conditions for checking:
    1. Scores are similar (difference < threshold)
    2. Different precedence levels
    
    Args:
        ranked_chunks: List of chunks with scores
        question: Original question
        score_threshold: Maximum score difference to consider similar
        
    Returns:
        Conflict info if detected, None otherwise
    """
    if len(ranked_chunks) < 2:
        return None
    
    # Extract chunks and scores
    chunk1, score1 = _extract_chunk_and_score(ranked_chunks[0])
    chunk2, score2 = _extract_chunk_and_score(ranked_chunks[1])
    
    if chunk1 is None or chunk2 is None:
        return None
    
    # Check score similarity
    score_diff = abs(score1 - score2)
    if score_diff > score_threshold:
        # Scores too different, clear winner
        return None
    
    # Check precedence levels
    prec1 = getattr(chunk1, 'precedence_level', 1)
    prec2 = getattr(chunk2, 'precedence_level', 1)
    
    if prec1 == prec2:
        # Same precedence, no conflict concern
        return None
    
    # Potential conflict - use LLM to verify
    logger.info(f"Checking conflict between chunk {chunk1.id} (prec={prec1}) and {chunk2.id} (prec={prec2})")
    
    conflict = detect_conflict(chunk1, chunk2, question)
    
    if conflict["is_conflict"]:
        logger.warning(f"Conflict detected: {conflict['explanation']}")
    
    return conflict if conflict["is_conflict"] else None


def _extract_chunk_and_score(item) -> tuple:
    """Extract chunk and score from various formats."""
    if hasattr(item, 'chunk') and hasattr(item, 'final_score'):
        # ScoredChunk dataclass
        return item.chunk, item.final_score
    elif isinstance(item, tuple) and len(item) == 2:
        # (chunk, score) tuple
        return item[0], item[1]
    elif hasattr(item, 'similarity'):
        # RuleChunkSearchResult
        return item, getattr(item, 'similarity', 0.0)
    else:
        return None, 0.0


def generate_conflict_note(conflict: dict[str, Any]) -> str:
    """Generate a user-facing note about the conflict."""
    explanation = conflict.get("explanation", "")
    resolution = conflict.get("resolution", "")
    
    if resolution:
        return f"Note: {explanation} {resolution}"
    elif explanation:
        return f"Note: {explanation}"
    else:
        return "Note: Multiple sources provide different information about this rule."
