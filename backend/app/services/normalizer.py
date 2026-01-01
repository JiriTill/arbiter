"""
Question normalization logic for intelligent caching.
"""

import re
import logging

logger = logging.getLogger(__name__)

# Try to download NLTK data at module load
try:
    import nltk
    nltk.download('wordnet', quiet=True)
    nltk.download('omw-1.4', quiet=True)
    from nltk.stem import WordNetLemmatizer
    _lemmatizer = WordNetLemmatizer()
    NLTK_AVAILABLE = True
except Exception as e:
    logger.warning(f"NLTK not available, skipping lemmatization: {e}")
    _lemmatizer = None
    NLTK_AVAILABLE = False


def normalize_question(q: str) -> str:
    """
    Normalize a question string for consistent caching.
    
    Steps:
    1. Lowercase and strip
    2. Remove punctuation
    3. Collapse whitespace
    4. Convert number words to digits
    5. Lemmatize words (if NLTK available)
    """
    if not q:
        return ""

    # Lowercase
    q = q.lower().strip()
    
    # Remove punctuation
    q = re.sub(r'[^\w\s]', '', q)
    
    # Collapse whitespace
    q = re.sub(r'\s+', ' ', q)
    
    # Number words to digits
    number_map = {
        'one': '1', 'two': '2', 'three': '3', 'four': '4', 'five': '5',
        'six': '6', 'seven': '7', 'eight': '8', 'nine': '9', 'ten': '10',
        'eleven': '11', 'twelve': '12'
    }
    for word, digit in number_map.items():
        q = re.sub(r'\b' + word + r'\b', digit, q)
    
    # Lemmatize (convert words to base form) - skip if NLTK not available
    if NLTK_AVAILABLE and _lemmatizer:
        try:
            words = q.split()
            words = [_lemmatizer.lemmatize(w) for w in words]
            q = ' '.join(words)
        except Exception as e:
            logger.warning(f"Lemmatization failed: {e}")
    
    return q

