"""Business logic services for The Arbiter."""

from app.services.chunker import (
    Chunk,
    chunk_text,
    chunk_document,
    split_into_sentences,
    estimate_tokens,
)
from app.services.embeddings import (
    create_embedding,
    batch_create_embeddings,
    get_embedding_model_info,
    EMBEDDING_MODEL,
    EMBEDDING_DIMENSIONS,
)
from app.services.ingestion import (
    IngestionResult,
    ingest_source,
    ingest_all_pending,
    download_pdf,
    extract_text_from_pdf,
    compute_file_hash,
)
from app.services.answer_generator import (
    generate_answer,
    generate_answer_with_verification,
    estimate_answer_quality,
    ANSWER_MODEL,
)
from app.services.citation_verifier import (
    verify_citation,
    verify_citation_in_any_chunk,
    get_relevant_sections,
    normalize_text,
)
from app.services.levenshtein import (
    levenshtein_distance,
    similarity_ratio,
    find_best_match_window,
)
from app.services.retrieval import (
    hybrid_search,
    hybrid_search_sync,
)
from app.services.cache import (
    get_or_create_embedding,
    get_cached_embedding,
    cache_embedding,
    clear_embedding_cache,
    get_cache_stats,
)
from app.services.override_detector import (
    detect_overrides,
    detect_and_save_overrides,
    has_override_keywords,
)

__all__ = [
    # Chunker
    "Chunk",
    "chunk_text",
    "chunk_document",
    "split_into_sentences",
    "estimate_tokens",
    
    # Embeddings
    "create_embedding",
    "batch_create_embeddings",
    "get_embedding_model_info",
    "EMBEDDING_MODEL",
    "EMBEDDING_DIMENSIONS",
    
    # Ingestion
    "IngestionResult",
    "ingest_source",
    "ingest_all_pending",
    "download_pdf",
    "extract_text_from_pdf",
    "compute_file_hash",
    
    # Answer Generation
    "generate_answer",
    "generate_answer_with_verification",
    "estimate_answer_quality",
    "ANSWER_MODEL",
    
    # Citation Verification
    "verify_citation",
    "verify_citation_in_any_chunk",
    "get_relevant_sections",
    "normalize_text",
    
    # String Matching
    "levenshtein_distance",
    "similarity_ratio",
    "find_best_match_window",
    
    # Retrieval
    "hybrid_search",
    "hybrid_search_sync",
    
    # Cache
    "get_or_create_embedding",
    "get_cached_embedding",
    "cache_embedding",
    "clear_embedding_cache",
    "get_cache_stats",
    
    # Override Detection
    "detect_overrides",
    "detect_and_save_overrides",
    "has_override_keywords",
]
