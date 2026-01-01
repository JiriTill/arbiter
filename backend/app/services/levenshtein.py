"""
Levenshtein distance calculation for fuzzy string matching.
"""


def levenshtein_distance(s1: str, s2: str) -> int:
    """
    Calculate the Levenshtein (edit) distance between two strings.
    
    This is the minimum number of single-character edits (insertions,
    deletions, or substitutions) required to change one string into the other.
    
    Uses dynamic programming with O(min(m,n)) space complexity.
    
    Args:
        s1: First string
        s2: Second string
        
    Returns:
        The edit distance as an integer
    """
    # Make s1 the shorter string for space optimization
    if len(s1) > len(s2):
        s1, s2 = s2, s1
    
    m, n = len(s1), len(s2)
    
    # Edge cases
    if m == 0:
        return n
    if n == 0:
        return m
    
    # Previous and current row of distances
    prev_row = list(range(m + 1))
    curr_row = [0] * (m + 1)
    
    for j in range(1, n + 1):
        curr_row[0] = j
        
        for i in range(1, m + 1):
            if s1[i - 1] == s2[j - 1]:
                curr_row[i] = prev_row[i - 1]
            else:
                curr_row[i] = 1 + min(
                    prev_row[i],      # Deletion
                    curr_row[i - 1],  # Insertion
                    prev_row[i - 1],  # Substitution
                )
        
        # Swap rows
        prev_row, curr_row = curr_row, prev_row
    
    return prev_row[m]


def similarity_ratio(s1: str, s2: str) -> float:
    """
    Calculate similarity ratio between two strings (0.0 to 1.0).
    
    Higher = more similar. 1.0 = identical.
    
    Args:
        s1: First string
        s2: Second string
        
    Returns:
        Similarity ratio between 0.0 and 1.0
    """
    if not s1 and not s2:
        return 1.0
    if not s1 or not s2:
        return 0.0
    
    distance = levenshtein_distance(s1, s2)
    max_len = max(len(s1), len(s2))
    
    return 1.0 - (distance / max_len)


def find_best_match_window(target: str, source: str) -> tuple[str, int, int]:
    """
    Find the substring window in source that best matches target.
    
    Uses a sliding window approach to find the closest matching
    substring of approximately the same length as target.
    
    Args:
        target: The string to search for
        source: The string to search within
        
    Returns:
        Tuple of (best_match_substring, start_index, distance)
    """
    target_len = len(target)
    source_len = len(source)
    
    if target_len == 0:
        return ("", 0, 0)
    if source_len == 0:
        return ("", 0, target_len)
    
    # If target is longer than source, compare full strings
    if target_len >= source_len:
        return (source, 0, levenshtein_distance(target, source))
    
    best_match = ""
    best_start = 0
    best_distance = float('inf')
    
    # Window sizes to try: exact length, +/- 10%
    window_sizes = [
        target_len,
        int(target_len * 0.9),
        int(target_len * 1.1),
        int(target_len * 0.95),
        int(target_len * 1.05),
    ]
    
    for window_size in window_sizes:
        if window_size <= 0 or window_size > source_len:
            continue
        
        # Step size for sliding (faster for long texts)
        step = max(1, window_size // 20)
        
        for start in range(0, source_len - window_size + 1, step):
            window = source[start:start + window_size]
            distance = levenshtein_distance(target, window)
            
            if distance < best_distance:
                best_distance = distance
                best_match = window
                best_start = start
                
                # Early termination if we found an exact match
                if distance == 0:
                    return (best_match, best_start, best_distance)
    
    return (best_match, best_start, int(best_distance))
