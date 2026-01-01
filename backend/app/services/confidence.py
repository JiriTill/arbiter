"""
Confidence calculation logic for The Arbiter.
Determines verdict confidence based on strict mathematical thresholds.
"""

from typing import Any


def get_low_reason(verify_ok: bool, s_top: float, conflict: bool) -> str:
    """Determine reason for low confidence."""
    if not verify_ok:
        return 'Could not verify exact quote'
    if conflict:
        return 'Multiple sources conflict'
    if s_top < 0.70:
        return 'Weak semantic match'
    return 'Ambiguous ruling'


def calculate_confidence(context: dict[str, Any]) -> tuple[str, dict[str, str]]:
    """
    Calculate confidence level and provide reason.
    
    Args:
        context: Dictionary containing:
            - verify_ok: bool (citation verified)
            - s_top: float (top chunk score, 0-1)
            - s_gap: float (score difference between top 2 chunks)
            - conflict: bool (contradictory sources detected)
            - coverage: int (tracked for analytics, unused in logic)
            
    Returns:
        Tuple of (confidence_level, reason_dict)
        confidence_level: 'high' | 'medium' | 'low'
        reason_dict: {'reason': string}
    """
    verify_ok = context.get('verify_ok', False)
    s_top = context.get('s_top', 0.0)
    s_gap = context.get('s_gap', 0.0)
    conflict = context.get('conflict', False)
    
    # High confidence
    # Strict requirements: Verified, strong match, clear winner, no conflict
    if verify_ok and s_top >= 0.85 and s_gap >= 0.08 and not conflict:
        return 'high', {'reason': 'Strong match, verified quote, no conflicts'}
    
    # Medium confidence
    # Requirements: Verified, decent match, no conflict
    if verify_ok and s_top >= 0.70 and not conflict:
        return 'medium', {'reason': 'Good match, verified quote'}
    
    # Low confidence
    # Anything else falls here
    reason = get_low_reason(verify_ok, s_top, conflict)
    return 'low', {'reason': reason}
