"""
Answer generation service using OpenAI.
Generates structured answers from retrieved rule chunks.
"""

import json
import logging
import re
from typing import Any

from openai import OpenAI

from app.config import get_settings
from app.db.models import RuleChunk, RuleChunkSearchResult


# Configure logging
logger = logging.getLogger(__name__)

# Model configuration
ANSWER_MODEL = "gpt-4o-mini"
MAX_TOKENS = 1000


# Prompt template for answer generation
SYSTEM_PROMPT = """You are a precise board game rules arbiter. Your role is to answer rules questions accurately using ONLY the provided rule excerpts. Be helpful but strictly accurate.

Important rules:
1. Only use information from the provided excerpts
2. If the excerpts don't contain enough information, say so
3. Quote exactly from the source, don't paraphrase
4. Be confident when rules are clear, note ambiguity when unclear
5. Always provide the chunk_id and page number for your citation"""


def get_openai_client() -> OpenAI:
    """Get configured OpenAI client."""
    settings = get_settings()
    if not settings.openai_api_key:
        raise ValueError("OPENAI_API_KEY not configured")
    return OpenAI(api_key=settings.openai_api_key)


def format_chunks_for_prompt(chunks: list[RuleChunk | RuleChunkSearchResult]) -> str:
    """Format chunks as context for the prompt."""
    formatted = []
    for chunk in chunks:
        chunk_id = getattr(chunk, 'id', 0)
        page = chunk.page_number
        text = chunk.chunk_text
        source_type = getattr(chunk, 'source_type', 'rulebook')
        
        formatted.append(f"""[Chunk {chunk_id}] (Page {page}, {source_type})
{text}
""")
    
    return "\n---\n".join(formatted)


def generate_answer(
    question: str,
    chunks: list[RuleChunk | RuleChunkSearchResult],
    game_name: str,
    edition: str | None = None,
) -> dict[str, Any]:
    """
    Generate an answer to a rules question using retrieved chunks.
    
    Args:
        question: The user's rules question
        chunks: Retrieved relevant rule chunks
        game_name: Name of the game
        edition: Optional edition string
        
    Returns:
        Dict with verdict, quote, confidence, etc.
    """
    if not chunks:
        return {
            "verdict": "Unable to answer - no rule excerpts found for this game.",
            "quote_exact": "",
            "quote_chunk_id": None,
            "page": None,
            "source_type": "rulebook",
            "confidence": "low",
            "notes": ["No indexed rules found for this game. The rulebook may not be ingested yet."],
        }
    
    # Format chunks for context
    chunks_text = format_chunks_for_prompt(chunks)
    
    # Build the user prompt
    edition_str = f" ({edition})" if edition else ""
    user_prompt = f"""Game: {game_name}{edition_str}

Question: {question}

Rule Excerpts:
{chunks_text}

Based on these excerpts, answer the question. Provide your response as valid JSON with this exact structure:
{{
  "verdict": "YES/NO/It depends + clear explanation of the rule",
  "quote_exact": "exact verbatim quote from one excerpt (max 100 words)",
  "quote_chunk_id": the_chunk_id_number,
  "page": page_number,
  "source_type": "rulebook or faq or errata",
  "confidence": "high or medium or low",
  "notes": ["optional array", "of additional notes"]
}}

Respond ONLY with the JSON, no other text."""

    client = get_openai_client()
    
    try:
        response = client.chat.completions.create(
            model=ANSWER_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=MAX_TOKENS,
            temperature=0.1,  # Low temperature for consistency
        )
        
        content = response.choices[0].message.content
        
        # Parse JSON response
        result = parse_answer_json(content)
        
        # Add usage info
        if response.usage:
            result["_usage"] = {
                "input_tokens": response.usage.prompt_tokens,
                "output_tokens": response.usage.completion_tokens,
                "model": response.model
            }
        
        # Validate and fix the response
        result = validate_and_fix_response(result, chunks)
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to generate answer: {e}")
        return {
            "verdict": f"Error generating answer: {str(e)}",
            "quote_exact": "",
            "quote_chunk_id": None,
            "page": None,
            "source_type": "rulebook",
            "confidence": "low",
            "notes": ["An error occurred while generating the answer."],
        }


def parse_answer_json(content: str) -> dict[str, Any]:
    """Parse JSON from LLM response, handling common issues."""
    if not content:
        return {}
    
    # Try direct JSON parse first
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass
    
    # Try to extract JSON from markdown code blocks
    json_match = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', content, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass
    
    # Try to find JSON object in content
    json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', content, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(0))
        except json.JSONDecodeError:
            pass
    
    # Return minimal response if parsing fails
    logger.warning(f"Failed to parse JSON from response: {content[:200]}...")
    return {
        "verdict": content[:500] if content else "Unable to parse response",
        "confidence": "low",
        "notes": ["Response parsing failed"],
    }


def validate_and_fix_response(
    result: dict[str, Any],
    chunks: list[RuleChunk | RuleChunkSearchResult],
) -> dict[str, Any]:
    """Validate and fix the LLM response."""
    
    # Ensure required fields exist
    if "verdict" not in result:
        result["verdict"] = "Unable to determine"
    
    if "confidence" not in result:
        result["confidence"] = "low"
    elif result["confidence"] not in ("high", "medium", "low"):
        result["confidence"] = "medium"
    
    if "quote_exact" not in result:
        result["quote_exact"] = ""
    
    if "quote_chunk_id" not in result:
        result["quote_chunk_id"] = None
    
    if "page" not in result:
        result["page"] = None
    
    if "source_type" not in result:
        result["source_type"] = "rulebook"
    
    if "notes" not in result:
        result["notes"] = []
    elif not isinstance(result["notes"], list):
        result["notes"] = [result["notes"]]
    
    # Validate chunk_id exists in our chunks
    if result["quote_chunk_id"] is not None:
        chunk_ids = {getattr(c, 'id', 0) for c in chunks}
        if result["quote_chunk_id"] not in chunk_ids:
            # LLM hallucinated a chunk ID, try to find the correct one
            if chunks:
                # Default to first chunk
                first_chunk = chunks[0]
                result["quote_chunk_id"] = getattr(first_chunk, 'id', None)
                result["page"] = first_chunk.page_number
                result["notes"].append("Note: Citation was corrected automatically.")
    
    return result


from app.services.confidence import calculate_confidence

def estimate_answer_quality(
    result: dict[str, Any],
    chunks: list[RuleChunk | RuleChunkSearchResult],
) -> tuple[str, str]:
    """
    Estimate the quality/confidence of an answer.
    
    Returns:
        Tuple of (confidence_level, reason)
        confidence_level: "high" | "medium" | "low"
    """
    # 1. Get verification status
    verify_ok = result.get("verified_quote", False)
    
    # 2. Get retrieval scores
    s_top = 0.0
    s_gap = 0.0
    
    if chunks and chunks[0]:
        first = chunks[0]
        # Check if we have score (RuleChunkSearchResult) or just RuleChunk
        if hasattr(first, 'score') and isinstance(first.score, (int, float)):
            s_top = float(first.score)
            
            if len(chunks) > 1 and chunks[1]:
                second = chunks[1]
                if hasattr(second, 'score') and isinstance(second.score, (int, float)):
                    s_gap = s_top - float(second.score)
    
    # 3. Check for conflict
    # Conflict is present if we have a conflict_note
    conflict = bool(result.get("conflict_note"))
    
    # 4. Calculate confidence
    context = {
        "verify_ok": verify_ok,
        "s_top": s_top,
        "s_gap": s_gap,
        "conflict": conflict,
    }
    
    confidence, details = calculate_confidence(context)
    return confidence, details['reason']


# Stricter prompt for regeneration attempts
STRICT_SYSTEM_PROMPT = """You are a precise board game rules arbiter. Your role is to answer rules questions accurately using ONLY the provided rule excerpts.

CRITICAL RULES:
1. ONLY quote EXACT, VERBATIM text from the provided excerpts
2. Do NOT paraphrase, summarize, or modify quotes in any way
3. Copy the quote character-for-character from the excerpt
4. If you cannot find a good verbatim quote, use an empty string
5. Always provide the exact chunk_id the quote comes from
6. Be accurate above all else"""


def generate_answer_strict(
    question: str,
    chunks: list[RuleChunk | RuleChunkSearchResult],
    game_name: str,
    edition: str | None = None,
) -> dict[str, Any]:
    """
    Generate answer with stricter quote requirements.
    Used as second attempt after verification failure.
    """
    if not chunks:
        return generate_answer(question, chunks, game_name, edition)
    
    chunks_text = format_chunks_for_prompt(chunks)
    edition_str = f" ({edition})" if edition else ""
    
    user_prompt = f"""Game: {game_name}{edition_str}

Question: {question}

Rule Excerpts:
{chunks_text}

IMPORTANT: You MUST quote EXACTLY from the excerpts above. Copy text verbatim - do not paraphrase.

Respond with valid JSON:
{{
  "verdict": "YES/NO/It depends + clear explanation",
  "quote_exact": "VERBATIM quote copied exactly from an excerpt (or empty string if unsure)",
  "quote_chunk_id": the_chunk_id_number_the_quote_is_from,
  "page": page_number,
  "source_type": "rulebook or faq or errata",
  "confidence": "high or medium or low",
  "notes": []
}}

Only JSON, no other text."""

    client = get_openai_client()
    
    try:
        response = client.chat.completions.create(
            model=ANSWER_MODEL,
            messages=[
                {"role": "system", "content": STRICT_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=MAX_TOKENS,
            temperature=0.0,  # Zero temperature for maximum determinism
        )
        
        content = response.choices[0].message.content
        result = parse_answer_json(content)
        result = validate_and_fix_response(result, chunks)
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to generate strict answer: {e}")
        return generate_answer(question, chunks, game_name, edition)


def generate_answer_with_verification(
    question: str,
    chunks: list[RuleChunk | RuleChunkSearchResult],
    game_name: str,
    edition: str | None = None,
    conflict_note: str | None = None,
) -> dict[str, Any]:
    """
    Generate an answer with citation verification and regeneration fallback.
    
    Process:
    1. Generate initial answer
    2. Verify the citation
    3. If verification fails, regenerate with stricter prompt
    4. Verify again
    5. If still fails, return fallback response
    
    Args:
        question: The user's rules question
        chunks: Retrieved relevant rule chunks
        game_name: Name of the game
        edition: Optional edition string
        conflict_note: Note about detected rule conflicts
        
    Returns:
        Dict with verdict, verified_quote, and other fields
    """
    from app.services.citation_verifier import (
        verify_citation,
        get_relevant_sections,
    )
    
    if not chunks:
        return {
            "verdict": "Unable to answer - no rule excerpts found for this game.",
            "quote_exact": "",
            "quote_chunk_id": None,
            "page": None,
            "source_type": "rulebook",
            "confidence": "low",
            "verified_quote": False,
            "notes": ["No indexed rules found for this game."],
        }
    
    # ========================================================================
    # First Attempt
    # ========================================================================
    
    logger.info("Generating answer (attempt 1)...")
    result = generate_answer(question, chunks, game_name, edition)
    
    # Verify citation if we have one
    if result.get("quote_exact") and result.get("quote_chunk_id"):
        verification = verify_citation(
            quote=result["quote_exact"],
            chunk_id=result["quote_chunk_id"],
            chunks=chunks,
        )
        
        if verification["verified"]:
            result["verified_quote"] = True
            result["verification_method"] = verification["method"]
            if verification.get("distance"):
                result["verification_distance"] = verification["distance"]
            
            # Add conflict note if present
            if conflict_note:
                result["conflict_note"] = conflict_note
                notes = result.get("notes", [])
                notes.append(conflict_note)
                result["notes"] = notes
            
            logger.info(f"Citation verified on first attempt ({verification['method']})")
            return result
        
        logger.warning("Citation verification failed on first attempt")
    
    # ========================================================================
    # Second Attempt (Stricter)
    # ========================================================================
    
    logger.info("Regenerating answer with stricter prompt (attempt 2)...")
    result = generate_answer_strict(question, chunks, game_name, edition)
    
    # Verify again
    if result.get("quote_exact") and result.get("quote_chunk_id"):
        verification = verify_citation(
            quote=result["quote_exact"],
            chunk_id=result["quote_chunk_id"],
            chunks=chunks,
        )
        
        if verification["verified"]:
            result["verified_quote"] = True
            result["verification_method"] = verification["method"]
            if verification.get("distance"):
                result["verification_distance"] = verification["distance"]
            
            # Add conflict note if present
            if conflict_note:
                result["conflict_note"] = conflict_note
                notes = result.get("notes", [])
                notes.append(conflict_note)
                result["notes"] = notes
            
            logger.info(f"Citation verified on second attempt ({verification['method']})")
            return result
        
        logger.warning("Citation verification failed on second attempt")
    
    # ========================================================================
    # Fallback Response
    # ========================================================================
    
    logger.warning("Both attempts failed verification, returning fallback response")
    
    # Build fallback notes
    notes = [
        "Could not verify exact quote from rulebook.",
        "Please review the relevant sections above for the authoritative answer.",
    ]
    
    # Add conflict note if present
    if conflict_note:
        notes.insert(0, conflict_note)
    
    # Build fallback response without unverified quote
    fallback = {
        "verdict": result.get("verdict", "Based on relevant sections in the rulebook..."),
        "quote_exact": "",
        "quote_chunk_id": None,
        "page": None,
        "source_type": "rulebook",
        "confidence": "low",
        "verified_quote": False,
        "relevant_sections": get_relevant_sections(chunks, max_sections=3),
        "notes": notes,
    }
    
    if conflict_note:
        fallback["conflict_note"] = conflict_note
    
    # If we have a verdict that looks reasonable, use it
    verdict = result.get("verdict", "")
    if verdict and len(verdict) > 20:
        fallback["verdict"] = f"Based on relevant sections: {verdict}"
    
    return fallback

