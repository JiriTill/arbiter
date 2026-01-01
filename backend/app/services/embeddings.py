"""
Embedding generation service using OpenAI.
Handles single and batch embedding creation for RAG.
"""

import logging
from typing import Any

from openai import OpenAI

from app.config import get_settings


# Configure logging
logger = logging.getLogger(__name__)

# Model configuration
EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSIONS = 1536
BATCH_SIZE = 100  # OpenAI recommends max 2048, but smaller is safer


def get_openai_client() -> OpenAI:
    """Get configured OpenAI client."""
    settings = get_settings()
    if not settings.openai_api_key:
        raise ValueError("OPENAI_API_KEY not configured")
    return OpenAI(api_key=settings.openai_api_key)


def create_embedding(text: str) -> list[float]:
    """
    Create embedding for a single text.
    
    Args:
        text: Text to embed (will be truncated if too long)
        
    Returns:
        List of 1536 floats representing the embedding
        
    Raises:
        ValueError: If text is empty
        openai.APIError: If API call fails
    """
    if not text or not text.strip():
        raise ValueError("Cannot create embedding for empty text")
    
    # OpenAI has a token limit; truncate if needed
    # text-embedding-3-small supports 8192 tokens
    # Rough estimate: 4 chars per token, so ~32000 chars max
    if len(text) > 30000:
        logger.warning(f"Truncating text from {len(text)} to 30000 chars for embedding")
        text = text[:30000]
    
    client = get_openai_client()
    
    try:
        response = client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=text,
            dimensions=EMBEDDING_DIMENSIONS,
        )
        return response.data[0].embedding
    except Exception as e:
        logger.error(f"Failed to create embedding: {e}")
        raise


def batch_create_embeddings(
    texts: list[str],
    batch_size: int = BATCH_SIZE,
) -> list[list[float]]:
    """
    Create embeddings for multiple texts in batches.
    
    Args:
        texts: List of texts to embed
        batch_size: Number of texts per API call (default 100)
        
    Returns:
        List of embeddings in same order as input texts
        
    Raises:
        ValueError: If texts is empty
        openai.APIError: If API call fails
    """
    if not texts:
        return []
    
    # Filter and prepare texts
    processed_texts: list[str] = []
    for text in texts:
        if not text or not text.strip():
            processed_texts.append("")  # Will handle later
        elif len(text) > 30000:
            processed_texts.append(text[:30000])
        else:
            processed_texts.append(text)
    
    client = get_openai_client()
    all_embeddings: list[list[float]] = []
    
    # Process in batches
    for i in range(0, len(processed_texts), batch_size):
        batch = processed_texts[i:i + batch_size]
        batch_indices = list(range(i, min(i + batch_size, len(processed_texts))))
        
        # Filter out empty texts for this batch
        non_empty_texts: list[str] = []
        non_empty_indices: list[int] = []
        
        for idx, text in zip(batch_indices, batch):
            if text.strip():
                non_empty_texts.append(text)
                non_empty_indices.append(idx - i)  # Local index in batch
        
        if not non_empty_texts:
            # All texts in batch are empty, use zero vectors
            all_embeddings.extend([[0.0] * EMBEDDING_DIMENSIONS for _ in batch])
            continue
        
        try:
            logger.info(f"Creating embeddings for batch {i // batch_size + 1} "
                       f"({len(non_empty_texts)} texts)")
            
            response = client.embeddings.create(
                model=EMBEDDING_MODEL,
                input=non_empty_texts,
                dimensions=EMBEDDING_DIMENSIONS,
            )
            
            # Map embeddings back to batch positions
            batch_embeddings: list[list[float]] = [[0.0] * EMBEDDING_DIMENSIONS for _ in batch]
            for j, embedding_data in enumerate(response.data):
                local_idx = non_empty_indices[j]
                batch_embeddings[local_idx] = embedding_data.embedding
            
            all_embeddings.extend(batch_embeddings)
            
        except Exception as e:
            logger.error(f"Failed to create batch embeddings: {e}")
            raise
    
    return all_embeddings


def count_tokens_estimate(text: str) -> int:
    """
    Estimate token count for text.
    Rough approximation for planning purposes.
    """
    return len(text) // 4


def get_embedding_model_info() -> dict[str, Any]:
    """Get information about the embedding model being used."""
    return {
        "model": EMBEDDING_MODEL,
        "dimensions": EMBEDDING_DIMENSIONS,
        "batch_size": BATCH_SIZE,
        "max_input_tokens": 8192,
    }
