"""
Question normalization logic for intelligent caching.
"""

import re
from nltk.stem import WordNetLemmatizer


def normalize_question(q: str) -> str:
    """
    Normalize a question string for consistent caching.
    
    Steps:
    1. Lowercase and strip
    2. Remove punctuation
    3. Collapse whitespace
    4. Convert number words to digits
    5. Lemmatize words
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
    
    # Lemmatize (convert words to base form)
    # Note: Requires nltk.download('wordnet') and nltk.download('omw-1.4')
    lemmatizer = WordNetLemmatizer()
    words = q.split()
    words = [lemmatizer.lemmatize(w) for w in words]
    
    return ' '.join(words)
