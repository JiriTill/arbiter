"""
Text chunking utilities for RAG ingestion.
Splits text into overlapping chunks suitable for embedding.
"""

import re
from dataclasses import dataclass


@dataclass
class Chunk:
    """A text chunk with metadata."""
    page_number: int
    chunk_index: int
    chunk_text: str
    char_count: int
    estimated_tokens: int


def estimate_tokens(text: str) -> int:
    """
    Estimate token count for text.
    Rough approximation: 1 token ≈ 4 characters for English text.
    """
    return len(text) // 4


def split_into_sentences(text: str) -> list[str]:
    """
    Split text into sentences using regex.
    Handles common abbreviations and edge cases.
    """
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    if not text:
        return []
    
    # Split on sentence boundaries
    # This regex handles:
    # - Period, exclamation, question mark followed by space and capital
    # - Handles common abbreviations (Mr., Mrs., Dr., etc.)
    # - Preserves numbers with decimals (3.14)
    
    # First, protect common abbreviations
    protected = text
    abbreviations = [
        (r'Mr\.', 'Mr<<DOT>>'),
        (r'Mrs\.', 'Mrs<<DOT>>'),
        (r'Ms\.', 'Ms<<DOT>>'),
        (r'Dr\.', 'Dr<<DOT>>'),
        (r'Prof\.', 'Prof<<DOT>>'),
        (r'Jr\.', 'Jr<<DOT>>'),
        (r'Sr\.', 'Sr<<DOT>>'),
        (r'Inc\.', 'Inc<<DOT>>'),
        (r'Ltd\.', 'Ltd<<DOT>>'),
        (r'Corp\.', 'Corp<<DOT>>'),
        (r'vs\.', 'vs<<DOT>>'),
        (r'e\.g\.', 'e<<DOT>>g<<DOT>>'),
        (r'i\.e\.', 'i<<DOT>>e<<DOT>>'),
        (r'etc\.', 'etc<<DOT>>'),
        (r'(\d)\.(\d)', r'\1<<DECIMAL>>\2'),  # Decimal numbers
    ]
    
    for pattern, replacement in abbreviations:
        protected = re.sub(pattern, replacement, protected, flags=re.IGNORECASE)
    
    # Split on sentence-ending punctuation
    sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', protected)
    
    # Restore protected text
    result = []
    for sent in sentences:
        restored = sent.replace('<<DOT>>', '.').replace('<<DECIMAL>>', '.')
        restored = restored.strip()
        if restored:
            result.append(restored)
    
    return result


def chunk_text(
    text: str,
    page_number: int,
    max_tokens: int = 400,
    overlap: float = 0.5,
    start_index: int = 0,
) -> list[Chunk]:
    """
    Chunk text into overlapping segments suitable for embedding.
    
    Args:
        text: The text to chunk
        page_number: Page number for metadata
        max_tokens: Target maximum tokens per chunk (default 400)
        overlap: Fraction of overlap between chunks (default 0.5 = 50%)
        start_index: Starting chunk index (for multi-page documents)
        
    Returns:
        List of Chunk objects with metadata
    """
    if not text or not text.strip():
        return []
    
    # Split into sentences
    sentences = split_into_sentences(text)
    
    if not sentences:
        # If no sentences detected, treat whole text as one sentence
        sentences = [text.strip()]
    
    chunks: list[Chunk] = []
    current_sentences: list[str] = []
    current_tokens = 0
    chunk_index = start_index
    
    # Calculate overlap in tokens
    overlap_tokens = int(max_tokens * overlap)
    
    for sentence in sentences:
        sentence_tokens = estimate_tokens(sentence)
        
        # If single sentence exceeds max, split it
        if sentence_tokens > max_tokens:
            # Flush current chunk if any
            if current_sentences:
                chunk_text_str = ' '.join(current_sentences)
                chunks.append(Chunk(
                    page_number=page_number,
                    chunk_index=chunk_index,
                    chunk_text=chunk_text_str,
                    char_count=len(chunk_text_str),
                    estimated_tokens=estimate_tokens(chunk_text_str),
                ))
                chunk_index += 1
                current_sentences = []
                current_tokens = 0
            
            # Split long sentence by words
            words = sentence.split()
            word_chunk: list[str] = []
            word_tokens = 0
            
            for word in words:
                word_token_count = estimate_tokens(word + ' ')
                if word_tokens + word_token_count > max_tokens and word_chunk:
                    chunk_text_str = ' '.join(word_chunk)
                    chunks.append(Chunk(
                        page_number=page_number,
                        chunk_index=chunk_index,
                        chunk_text=chunk_text_str,
                        char_count=len(chunk_text_str),
                        estimated_tokens=estimate_tokens(chunk_text_str),
                    ))
                    chunk_index += 1
                    
                    # Keep overlap words
                    overlap_word_count = max(1, len(word_chunk) // 2)
                    word_chunk = word_chunk[-overlap_word_count:]
                    word_tokens = sum(estimate_tokens(w + ' ') for w in word_chunk)
                
                word_chunk.append(word)
                word_tokens += word_token_count
            
            # Add remaining words
            if word_chunk:
                current_sentences = [' '.join(word_chunk)]
                current_tokens = word_tokens
            continue
        
        # Check if adding this sentence exceeds max
        if current_tokens + sentence_tokens > max_tokens and current_sentences:
            # Create chunk from current sentences
            chunk_text_str = ' '.join(current_sentences)
            chunks.append(Chunk(
                page_number=page_number,
                chunk_index=chunk_index,
                chunk_text=chunk_text_str,
                char_count=len(chunk_text_str),
                estimated_tokens=estimate_tokens(chunk_text_str),
            ))
            chunk_index += 1
            
            # Calculate overlap: keep sentences that fit in overlap_tokens
            overlap_sentences: list[str] = []
            overlap_token_count = 0
            
            for sent in reversed(current_sentences):
                sent_tokens = estimate_tokens(sent)
                if overlap_token_count + sent_tokens <= overlap_tokens:
                    overlap_sentences.insert(0, sent)
                    overlap_token_count += sent_tokens
                else:
                    break
            
            current_sentences = overlap_sentences
            current_tokens = overlap_token_count
        
        # Add sentence to current chunk
        current_sentences.append(sentence)
        current_tokens += sentence_tokens
    
    # Don't forget the last chunk
    if current_sentences:
        chunk_text_str = ' '.join(current_sentences)
        chunks.append(Chunk(
            page_number=page_number,
            chunk_index=chunk_index,
            chunk_text=chunk_text_str,
            char_count=len(chunk_text_str),
            estimated_tokens=estimate_tokens(chunk_text_str),
        ))
    
    return chunks


def chunk_document(
    pages: list[tuple[int, str]],
    max_tokens: int = 400,
    overlap: float = 0.5,
) -> list[Chunk]:
    """
    Chunk an entire document with multiple pages.
    
    Args:
        pages: List of (page_number, page_text) tuples
        max_tokens: Target maximum tokens per chunk
        overlap: Fraction of overlap between chunks
        
    Returns:
        List of all Chunk objects for the document
    """
    all_chunks: list[Chunk] = []
    chunk_index = 0
    
    for page_number, page_text in pages:
        page_chunks = chunk_text(
            text=page_text,
            page_number=page_number,
            max_tokens=max_tokens,
            overlap=overlap,
            start_index=chunk_index,
        )
        all_chunks.extend(page_chunks)
        
        if page_chunks:
            chunk_index = page_chunks[-1].chunk_index + 1
    
    return all_chunks
